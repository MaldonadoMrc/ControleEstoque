# run.py

# A única coisa que este arquivo precisa fazer é importar
# a função de fábrica 'create_app' e criar uma instância do app.
from app import create_app

app = create_app()

# Esta condição garante que o servidor só rode quando
# executamos o arquivo diretamente (python run.py)
if __name__ == "__main__":
    app.run(debug=True)
