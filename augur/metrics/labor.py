#SPDX-License-Identifier: MIT
"""
Metrics that provide data about commits & their associated activity
"""

import datetime
import sqlalchemy as s
import pandas as pd
from augur.util import register_metric

@register_metric()
def committers(self, repo_group_id, repo_id=None, begin_date=None, end_date=None, period='month'):
    """
    :param repo_id: The repository's id
    :param repo_group_id: The repository's group id
    :param period: To set the periodicity to 'day', 'week', 'month' or 'year', defaults to 'day'
    :param begin_date: Specifies the begin date, defaults to '1970-1-1 00:00:00'
    :param end_date: Specifies the end date, defaults to datetime.now()
    :return: DataFrame of persons/period
    """
    if not begin_date:
        begin_date = '1970-1-1 00:00:01'
    if not end_date:
        end_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    committersSQL = None

    if repo_id:
        committersSQL = s.sql.text(
            """
				SELECT DATE,
                    b.repo_name,
                    rg_name,
					round( SUM ( estimated_labor_hours ), 2 ) AS estimated_hours 
				FROM
					(
					SELECT
						date_trunc(:period, labor.rl_analysis_date::date) as date, 
						A.repo_id,
						b.repo_name,
						programming_language,
						MAX ( A.rl_analysis_date) as analysis_date,
						SUM ( total_lines ) AS repo_total_lines,
						SUM ( code_lines ) AS repo_code_lines,
						SUM ( comment_lines ) AS repo_comment_lines,
						SUM ( blank_lines ) AS repo_blank_lines,
						AVG ( code_complexity ) AS repo_lang_avg_code_complexity,
						AVG ( code_complexity ) * SUM ( code_lines ) + 20 AS estimated_labor_hours 
					FROM
						repo_labor A,
						repo b,
						repo_groups 
					WHERE
						A.repo_id = b.repo_id 
						AND A.repo_id = :repo_id
						AND repo.repo_group_id = repo_groups.repo_group_id
						AND labor.rl_analysis_date BETWEEN :begin_date and :end_date
					GROUP BY
						A.repo_id,
						programming_language,
						repo_name 
					ORDER BY
						repo_name,
						A.repo_id,
						programming_language 
					) C 
				GROUP BY
					DATE,
					repo_id,
					repo_name 
				ORDER BY
					repo_name;

/*                SELECT DATE,
                    repo_name,
                    rg_name,
                    COUNT ( author_count ) 
                FROM
                    (
                    SELECT
                        date_trunc(:period, commits.cmt_author_date::date) as date,
                        repo_name,
                        rg_name,
                        cmt_author_name,
                        cmt_author_email,
                        COUNT ( cmt_author_name ) AS author_count 
                    FROM
                        commits, repo, repo_groups
                    WHERE
                        commits.repo_id = :repo_id AND commits.repo_id = repo.repo_id
                        AND repo.repo_group_id = repo_groups.repo_group_id
                        AND commits.cmt_author_date BETWEEN :begin_date and :end_date
                    GROUP BY date, repo_name, rg_name, cmt_author_name, cmt_author_email 
                    ORDER BY date DESC
                    ) C
                GROUP BY
                    C.DATE,
                    repo_name,
                    rg_name 
                ORDER BY C.DATE desc */
            """
        )
    else:
        committersSQL = s.sql.text(
            """
				SELECT DATE,
                    rg_name,
					round( SUM ( estimated_labor_hours ), 2 ) AS estimated_hours 
				FROM
					(
					SELECT
						date_trunc(:period, labor.rl_analysis_date::date) as date, 
						A.repo_id,
						b.repo_name,
						programming_language,
						MAX ( A.rl_analysis_date) as analysis_date,
						SUM ( total_lines ) AS repo_total_lines,
						SUM ( code_lines ) AS repo_code_lines,
						SUM ( comment_lines ) AS repo_comment_lines,
						SUM ( blank_lines ) AS repo_blank_lines,
						AVG ( code_complexity ) AS repo_lang_avg_code_complexity,
						AVG ( code_complexity ) * SUM ( code_lines ) + 20 AS estimated_labor_hours 
					FROM
						repo_labor A,
						repo b,
						repo_groups 
					WHERE
						A.repo_id = b.repo_id 
						AND A.repo_id = :repo_id
						AND repo.repo_group_id = repo_groups.repo_group_id
						AND labor.rl_analysis_date BETWEEN :begin_date and :end_date
					GROUP BY
						A.repo_id,
						programming_language,
						repo_name 
					ORDER BY
						repo_name,
						A.repo_id,
						programming_language 
					) C 
				GROUP BY
					repo_id,
					repo_name 
				ORDER BY
					repo_name; 
            """
        )

    results = pd.read_sql(committersSQL, self.database, params={'repo_id': repo_id, 
        'repo_group_id': repo_group_id,'begin_date': begin_date, 'end_date': end_date, 'period':period})

    return results


