import yaml
from github import Github
import networkx as nx
import re

config = None
with open('config.yml', 'r') as config_file:
    try:
        config = yaml.safe_load(config_file)
    except yaml.YAMLError as exc:
        print(exc)

try:
    G = nx.DiGraph()

    gh = Github(config['api_key'])
    org = gh.get_organization(config['org_scope'])
    repos = org.get_repos()

    org_count = 0
    for repo in repos:
        issues = repo.get_issues(sort='comments')
        for issue in issues[0:min(config['limit_repo'],issues.totalCount)]:
            # aumentar a contagem para a organização
            org_count += 1
            # obter as palavras a partir da label
            labels = issue.get_labels()
            words = [word.upper() for label in labels for word in re.split(r'\s|_|\-|\.|(?<=[a-z])(?=[A-Z])', label.name) if ':' not in word]
            # remover duplicatas
            words = list(words)
            # obter o login do autor
            login_author = issue.user.login
            # adicionar o nó
            G.add_node(login_author, type='user')
            # fazer a relação do autor com cada palavra
            for word in words:
                # adicionar o nó
                G.add_node(word, type='word')
                # fazer a relação do usuário com a palavra
                weight = G.get_edge_data(login_author, word)['weight'] + 1 if G.has_edge(login_author, word) else 1
                G.add_edge(login_author, word, weight=weight, type='user_word')
            # obter comentários
            comments = issue.get_comments()
            # fazer a relação do autor com cada um dos participantes
            for comment in comments:
                # obter o login do participante
                login_user = comment.user.login
                # adicionar o nó
                G.add_node(login_user, type='user')
                # verificar se é o autor
                if(login_user == login_author):
                    continue
                # fazer a relação com do usuário com o autor
                weight = G.get_edge_data(login_user, login_author)['weight'] + 1 if G.has_edge(login_user, login_author) else 1
                G.add_edge(login_user, login_author, weight=weight, type='user_user')
                # fazer a relação com cada uma das palavras
                for word in words:
                    # fazer a relação do usuário com a palavra
                    weight = G.get_edge_data(login_user, word)['weight'] + 1 if G.has_edge(login_user, word) else 1
                    G.add_edge(login_user, word, weight=weight, type='user_word')
            # checar a contagem de issues
            if(org_count >= config['limit_org']):
                break   
        # checar a contagem de issues
        if(org_count >= config['limit_org']):
            break
except Exception:
    pass

nx.write_graphml(G, config['output'])