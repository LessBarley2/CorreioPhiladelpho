from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.password_validation import MinimumLengthValidator, CommonPasswordValidator, NumericPasswordValidator
from django.core.exceptions import ValidationError
from django.contrib import messages
from .forms import LoginForm, CadastroForm
from usuarios.models import Usuario
from django.views.decorators.http import require_GET, require_POST
from utils.validadores import checar_caracteres_especiais_e_numeros
from json import loads
import email_validator

def entrar(request):
    form = LoginForm()

    if request.user.is_authenticated:
        return redirect('index')

    if request.method != 'POST':
        return render(request, 'usuarios/entrar.html', {'form': form})

    form = LoginForm(data=request.POST or None)

    if form.is_valid():
        email = request.POST.get('email')
        senha = request.POST.get('password')

        usuario = authenticate(request, email=email, password=senha)

        if not usuario:
            messages.error(request, 'E-mail ou senha inválidos')
            return render(request, 'usuarios/entrar.html', {'form': form})

        login(request, user=usuario)
        messages.success(request, f'Bem-vindo, {usuario.nome}')
        return redirect('index')
    else:
        return render(request, 'usuarios/entrar.html', {'form': form})

@require_GET
def registrar(request):
    form = CadastroForm()
    pagina_anterior = request.GET.get('proximo')

    if not pagina_anterior:
        pagina_anterior = '/'
    
    return render(request, 'usuarios/criar.html', {'form': form, 'proximo': pagina_anterior})

#Fetch API
@require_POST
def validacao_nome_registro(request):
    nome = loads(request.body)['valor']
    resposta = {}

    if checar_caracteres_especiais_e_numeros(nome):
        status = 400
        resposta['status'] = 'inválido'
        resposta['erro'] = 'Seu nome não pode conter caracteres especiais nem números'
    else:
        status = 200
        resposta['status'] = 'válido'

    return JsonResponse(resposta, status=status)

#Fetch API
@require_POST
def validacao_sobrenome_registro(request):
    sobrenome = loads(request.body)['valor']
    resposta = {}

    if checar_caracteres_especiais_e_numeros(sobrenome):
        status = 400
        resposta['status'] = 'inválido'
        resposta['erro'] = 'Seu sobrenome não pode conter caracteres especiais nem números'
    else:
        status = 200
        resposta['status'] = 'válido'

    return JsonResponse(resposta, status=status)

#Fetch API
@require_POST
def validacao_email_registro(request):
    email = loads(request.body)['valor']
    resposta = {}

    try:
        existente = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        existente = False
    
    try:
        valido = email_validator.validate_email(email)
    except email_validator.EmailSyntaxError as e:
        valido = False
    except:
        valido = False
    
    if not valido:
        status = 400
        resposta['status'] = 'inválido'
        resposta['erro'] = 'O e-mail digitado é inválido'
    elif existente:
        status = 409
        resposta['status'] = 'inválido'
        resposta['erro'] = 'Esse endereço já foi cadastrado'
    else:
        status = 200
        resposta['status'] = 'válido'

    return JsonResponse(resposta, status=status)

#Fetch API
@require_POST
def validacao_senha_registro(request):
    senha = loads(request.body)['valor']
    resposta = {}

    tamanho_minimo = MinimumLengthValidator(8)
    numerica = NumericPasswordValidator()
    comum = CommonPasswordValidator()

    # Checando se a senha tem no mínimo 8 caracteres
    try:
        tamanho_minimo.validate(senha)
    except ValidationError:
        tamanho_minimo = False

    # Checando se a senha é totalmente numérica
    try:
        numerica.validate(senha)
    except ValidationError:
        numerica = False

    # Checando se a senha é comum
    try:
        comum.validate(senha)
    except ValidationError:
        comum = False

    if not tamanho_minimo:
        status = 400
        resposta['status'] = 'inválido'
        resposta['erro'] = 'Sua senha deve conter pelo menos 8 caracteres'
    elif not numerica:
        status = 400
        resposta['status'] = 'inválido'
        resposta['erro'] = 'Sua senha não pode ser inteiramente numérica'
    elif not comum:
        status = 400
        resposta['status'] = 'inválido'
        resposta['erro'] = 'Essa senha é muito comum. Tente outra.'
    else:
        status = 200
        resposta['status'] = 'válido'

    return JsonResponse(resposta, status=status)

def sair(request):
    logout(request)

    return redirect('index')
