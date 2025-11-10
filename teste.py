from functions.utils import cadastrar_novo_usuario
form = {
  'cpf': '123.456.789-09',
  'email': 'teste@example.com',
  'telefone': '(11) 91234-5678',
  'matricula': '12345',
  'usuario': 'usuario_teste',
  'senha': 'senha123',
  'confirmarSenha': 'senha123'
}
print(cadastrar_novo_usuario(form))