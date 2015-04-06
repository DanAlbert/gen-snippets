import gerrit
import json
import sys

from datetime import date, timedelta


def get_week_range(week_of):
    monday = week_of - timedelta(days=week_of.weekday())
    return monday, monday + timedelta(days=6)


def change_url(change):
    """Generates a URL for a given change."""
    return '{base_url}/#/c/{number}'.format(
        base_url=gerrit.base_url,
        number=change['_number'])


def pretty_project_name(project_name):
    def strip_leading(component, path):
        if path.startswith(component):
            return path.partition('/')[2]
        return path

    project_name = strip_leading('platform/', project_name)
    project_name = strip_leading('external/', project_name)
    return project_name


def format_change(change):
    subject = change['subject']
    if subject.endswith('.'):
        subject = subject[:-1]
    url = change_url(change)
    status = ''
    if change['status'] == 'ABANDONED':
        status = 'ABANDONED '
    return '    * {}{}: {}'.format(status, subject, url)


def format_changes(header, changes):
    lines = []
    lines.append('* {}:'.format(header))
    for change in changes:
        lines.append(format_change(change))
    return lines


def make_snippets(topics, projects):
    lines = []
    for topic, changes in topics.items():
        lines.extend(format_changes(topic, changes))
    for project, changes in projects.items():
        lines.extend(format_changes(pretty_project_name(project), changes))
    return '\n'.join(lines).replace('_', r'\_')


def main():
    try:
        import userconfig
    except ImportError:
        sys.exit('userconfig.py not found')

    user = userconfig.username
    if len(sys.argv) == 2:
        year, month, day = [int(s) for s in sys.argv[1].split('-')]
        week_of = date(year, month, day)
    elif len(sys.argv) == 1:
        week_of = date.today() - timedelta(weeks=1)
    else:
        sys.exit('usage: python gen-snippets.py [YYYY-MM-DD]')
    monday, sunday = get_week_range(week_of)

    query = 'owner:{}+after:{}+before:{}'.format(user, monday, sunday)
    response = gerrit.call('/changes/?q={}'.format(query))
    changes = json.loads(response)

    project_names = {c['project'] for c in changes if 'topic' not in c}
    topic_names = {c['topic'] for c in changes if 'topic' in c}
    topics = {tn: [] for tn in topic_names}
    projects = {pn: [] for pn in project_names}
    for change in changes:
        if 'topic' in change and change['topic'] != '':
            topics[change['topic']].append(change)
        else:
            projects[change['project']].append(change)

    print make_snippets(topics, projects)


if __name__ == '__main__':
    main()
