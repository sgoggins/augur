
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