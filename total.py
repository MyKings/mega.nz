#!/usr/bin/env python
# coding: utf-8

import sys
import os
import subprocess
import re
import json
import imp

imp.reload(sys)
sys.setdefaultencoding('utf-8')


class Git(object):

    def __init__(self, git_search_path=('git', '/usr/bin/git', '/usr/local/bin/git', '/opt/local/bin/git')):
        """

        :param settings: django.conf.settings
        :param git_search_path:
        """
        self._git_path = ''
        regex = re.compile('git version [0-9]*\.[0-9]*\.[0-9]')

        for git_path in git_search_path:
            try:
                p = subprocess.Popen([git_path, '--version'],
                                     bufsize=1024,
                                     stdout=subprocess.PIPE)
            except OSError:
                pass
            else:
                self._git_path = git_path
                break
        else:
            raise Exception(
                'git program was not found in path. PATH is : {0}'.format(os.getenv('PATH'))
            )
        self._git_last_output = bytes.decode(p.communicate()[0])

        if regex.match(self._git_last_output):
            sys.stdout.write(self._git_last_output)
        else:
            sys.stdout.write('git program was not found in path.')


    def exec_cmd(self, cmd):
        """
        执行一个命令并返回
        :param cmd:
        :return:
        """
        _git_last_output = ''
        p = subprocess.Popen(cmd,
                             bufsize=100000,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             shell=True
                             )
        while p.poll() is None:
            output = p.stdout.readline()
            _git_last_output += output


        return _git_last_output #, git_err

    def get_config_url(self):
        cmd = "git config -l"
        output = self.exec_cmd(cmd)
        if output:
            for line in  output.split('\n'):
                if line.startswith('remote.origin.url='):
                    return line.replace('remote.origin.url=', '')
        return ''

    def get_author_list(self):
        cmd = "git log"
        output = self.exec_cmd(cmd)
        user_limit = {}
        result = []
        if output:
            user = ''
            for line in output.split('\n'):
                if line.startswith('Author:'):
                    user = line.replace('Author:', '').strip()

                if line.startswith('Date:') and user != '':
                    if user not in user_limit:
                        user_limit[user] = ''
                        result.append((user,  line.replace('Date:', '').strip()))
                        user = ''
                        continue
        return result

    def get_code_statistics(self, path):
        cmd = 'cloc --exclude-dir .git,locale, --exclude-ext=.jar,.zip,.md,.pyc,.dll,.po,.properties,*total.json --json ' + path
        output = self.exec_cmd(cmd)
        result = json.loads(output)
        lang = ''
        max_file = 0
        for k, v in result.iteritems():
            if k in ('header', 'SUM'):
                continue

            if v['nFiles'] > max_file:
                lang = k
                max_file = v['nFiles']

        return result, lang



if __name__ == '__main__':
    git = Git()
    base_path = os.path.dirname(os.path.realpath(__file__))
    print base_path
    result = {}
    for project in os.listdir('.'):
        project_path = os.path.join(base_path, project)
        if os.path.isdir(project_path):
            os.chdir(project_path)
            print project, project_path
            result[project] = {}
            result[project]['git'] = git.get_config_url()
            result[project]['author'] = []
            author_list = git.get_author_list()
            for author in author_list:
                result[project]['author'].append({'name': author[0], 'commit_time': author[1]})
            result[project]['cloc'], result[project]['lang'] = git.get_code_statistics(project_path)


    os.chdir(base_path)
    with open('./total.json', 'w') as fp:
        json.dump(result, fp, indent=2)
