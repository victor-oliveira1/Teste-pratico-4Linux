#!/usr/bin/env python3
# victor.oliveira@gmx.com

import subprocess
import os

def containers_executando():
    '''
    Retorna uma lista com o hostname e endereço IP de cada container iniciado.

    Necessário usar a função split() para separar o hostname do IP.
    Exemplo: ['app3.dexter.com.br 172.17.0.4', 'app2.dexter.com.br 172.17.0.3']
    '''
    containers = subprocess.check_output('docker inspect \
        --format "{{.Config.Hostname}} {{ .NetworkSettings.IPAddress }}" \
        $(docker ps -q)', shell=True).decode()
    lista = containers.split('\n')[:-1]
    return lista


def ubuntu_release():
    '''
    Retorna a versão do sistema operacional
    '''
    with open('/etc/os-release', 'r') as arquivo:
        texto = arquivo.read()
        for linha in texto.split():
            if linha.startswith('UBUNTU_CODENAME')\
               or linha.startswith('VERSION_CODENAME'):
                codename = linha.split('=')[1]
                if codename == 'xenial':
                    return codename
    print('Sistema operacional não suportado.')
    exit(1)

def executa_comando(cmd):
    '''
    Função para executar comandos e retornar True ou False,
    com base no código de retorno do comando.

    Retorno == 0: True
    Retorno != 0: False
    '''
    resultado = subprocess.run(cmd, shell=True).returncode
    if resultado == 0:
        return True
    return False

def verifica_root():
    uid = os.getuid()
    if uid != 0:
        print('É necessário executar este script como usuário root.')
        exit(1)

###########################################################################

verifica_root()
ubuntu_release()

print('Instalando dependências')
executa_comando('apt-get -y install \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common')

print('Instalando chave do repositório docker')
executa_comando('curl -fsSL https://download.docker.com/linux/ubuntu/gpg| \
    apt-key add -')

print('Configurando o repositório docker-ce')
executa_comando('add-apt-repository -y \
                "deb https://download.docker.com/linux/ubuntu \
                {} \
                stable"'.format(ubuntu_release()))

print('Atualizando repositório')
executa_comando('apt-get -y update')

print('Instalando o docker e nginx')
executa_comando('apt-get -y install nginx docker-ce')

print('Configurando container httpd')
executa_comando('docker pull httpd')
os.mkdir('/web')
for i in range(1,4):
    os.mkdir('/web/app{}'.format(i))
    with open('/web/app{}/index.html'.format(i), 'w') as arquivo:
        arquivo.write('''
<html>
<title>app{0}.dexter.com.br</title>
<body><center><h1>APP{0}</h1></center></body>
</html>
'''.format(i))
    executa_comando('docker run \
        --hostname app{0}.dexter.com.br \
        --name app{0} \
        -d \
        -v /web/app{0}:/usr/local/apache2/htdocs/ \
        httpd'.format(i))


print('Configurando Nginx')
for container in containers_executando():
    hostname, ip = container.split()
    with open('/etc/nginx/sites-available/dexter.com.br', 'a') as arquivo:
        arquivo.write('''
server {{
  server_name {};
        location / {{
          proxy_pass http://{}:80;
        }}
}}
'''.format(hostname, ip))
os.link('/etc/nginx/sites-available/dexter.com.br',
        '/etc/nginx/sites-enabled/dexter.com.br')
executa_comando('/etc/init.d/nginx restart')

print('Instalação e configuração OK\nEndereço IP dos contêineres:\n')
for linha in containers_executando():
    print(linha)
print('Muito obrigado 4Linux pela oportunidade!')

