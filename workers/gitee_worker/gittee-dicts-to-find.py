
        issues_insert = [
            {
                'repo_id': repo_id,
                'reporter_id': self.find_id_from_login(issue['user']['login']),
                'pull_request': issue['pull_request']['url'].split('/')[-1] if 'pull_request' in issue else None,
                'pull_request_id': issue['pull_request']['url'].split('/')[-1] if 'pull_request' in issue else None,
                'created_at': issue['created_at'],
                'issue_title': issue['title'],
                'issue_body': issue['body'].replace('0x00', '____') if issue['body'] else None,
                'comment_count': issue['comments'],
                'updated_at': issue['updated_at'],
                'closed_at': issue['closed_at'],
                'repository_url': issue['repository_url'],
                'issue_url': issue['url'],
                'labels_url': issue['labels_url'],
                'comments_url': issue['comments_url'],
                'events_url': issue['events_url'],
                'html_url': issue['html_url'],
                'issue_state': issue['state'],
                'issue_node_id': issue['node_id'],
                'gh_issue_id': issue['id'],
                'gh_issue_number': issue['number'],
                'gh_user_id': issue['user']['id'],
                'tool_source': self.tool_source,
                'tool_version': self.tool_version,
                'data_source': self.data_source
            } for issue in source_issues['insert']
        ]


        issue_comments_insert = [
            {
                'pltfrm_id': self.platform_id,
                'msg_text': comment['body'],
                'msg_timestamp': comment['created_at'],
                'cntrb_id': self.find_id_from_login(comment['user']['login']),
                'tool_source': self.tool_source,
                'tool_version': self.tool_version,
                'data_source': self.data_source
            } for comment in issue_comments['insert']
        ]

### This one would go into the worker_base.py

   def query_gitlab_contribtutors(self, entry_info, repo_id):

        gitlab_url = entry_info['given']['gitlab_url'] if 'gitlab_url' in entry_info['given'] else entry_info['given']['git_url']

        self.logger.info("Querying contributors with given entry info: " + str(entry_info) + "\n")

        path = urlparse(gitlab_url)
        split = path[2].split('/')

        owner = split[1]
        name = split[2]

        # Handles git url case by removing the extension
        if ".git" in name:
            name = name[:-4]

        url_encoded_format = quote(owner + '/' + name, safe='')

        table = 'contributors'
        table_pkey = 'cntrb_id'
        ### %TODO Remap this to a GitLab Contributor ID like the GitHub Worker. 
        ### Following Gabe's rework of the contributor worker. 
        update_col_map = {'cntrb_email': 'email'}
        duplicate_col_map = {'cntrb_login': 'email'}

        # list to hold contributors needing insertion or update
        contributors = self.paginate("https://gitlab.com/api/v4/projects/" + url_encoded_format + "/repository/contributors?per_page=100&page={}", duplicate_col_map, update_col_map, table, table_pkey, platform='gitlab')

        for repo_contributor in contributors:
            try:
                cntrb_compressed_url = ("https://gitlab.com/api/v4/users?search=" + repo_contributor['email'])
                self.logger.info("Hitting endpoint: " + cntrb_compressed_url + " ...\n")
                r = requests.get(url=cntrb_compressed_url, headers=self.headers)
                contributor_compressed = r.json()

                email = repo_contributor['email']
                self.logger.info(contributor_compressed)
                if len(contributor_compressed) == 0 or type(contributor_compressed) is dict or "id" not in contributor_compressed[0]:
                    continue

                self.logger.info("Fetching for user: " + str(contributor_compressed[0]["id"]))

                cntrb_url = ("https://gitlab.com/api/v4/users/" + str(contributor_compressed[0]["id"]))
                self.logger.info("Hitting end point to get complete contributor info now: " + cntrb_url + "...\n")
                r = requests.get(url=cntrb_url, headers=self.headers)
                contributor = r.json()

                cntrb = {
                    "cntrb_login": contributor.get('username', None),
                    "cntrb_created_at": contributor.get('created_at', None),
                    "cntrb_email": email,
                    "cntrb_company": contributor.get('organization', None),
                    "cntrb_location": contributor.get('location', None),
                    # "cntrb_type": , dont have a use for this as of now ... let it default to null
                    "cntrb_canonical": contributor.get('public_email', None),
                    "gh_user_id": contributor.get('id', None),
                    "gh_login": contributor.get('username', None),
                    "gh_url": contributor.get('web_url', None),
                    "gh_html_url": contributor.get('web_url', None),
                    "gh_node_id": None,
                    "gh_avatar_url": contributor.get('avatar_url', None),
                    "gh_gravatar_id": None,
                    "gh_followers_url": None,
                    "gh_following_url": None,
                    "gh_gists_url": None,
                    "gh_starred_url": None,
                    "gh_subscriptions_url": None,
                    "gh_organizations_url": None,
                    "gh_repos_url": None,
                    "gh_events_url": None,
                    "gh_received_events_url": None,
                    "gh_type": None,
                    "gh_site_admin": None,
                    "tool_source": self.tool_source,
                    "tool_version": self.tool_version,
                    "data_source": self.data_source
                }

                # Commit insertion to table
                if repo_contributor['flag'] == 'need_update':
                    result = self.db.execute(self.contributors_table.update().where(
                        self.worker_history_table.c.cntrb_email == email).values(cntrb))
                    self.logger.info("Updated tuple in the contributors table with existing email: {}".format(email))
                    self.cntrb_id_inc = repo_contributor['pkey']
                elif repo_contributor['flag'] == 'need_insertion':
                    result = self.db.execute(self.contributors_table.insert().values(cntrb))
                    self.logger.info("Primary key inserted into the contributors table: {}".format(result.inserted_primary_key))
                    self.results_counter += 1

                    self.logger.info("Inserted contributor: " + contributor['username'] + "\n")

                    # Increment our global track of the cntrb id for the possibility of it being used as a FK
                    self.cntrb_id_inc = int(result.inserted_primary_key[0])

            except Exception as e:
                self.logger.info("Caught exception: {}".format(e))
                self.logger.info("Cascading Contributor Anomalie from missing repo contributor data: {} ...\n".format(cntrb_url))
                continue