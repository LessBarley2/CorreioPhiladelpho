from django.shortcuts import render, redirect, get_object_or_404
from utils.feedback import incluir_feedback
from utils.professores import professor_requerido
from utils.redirecionamento import definir_url_anterior
from django.views.decorators.http import require_GET, require_POST
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from inicio.models import Comentario
from json import loads
from inicio.models import Post
from inicio.forms import PostForm, PostForm
from django.core.exceptions import ObjectDoesNotExist

@require_GET
@professor_requerido
def geral(request):
    form = incluir_feedback(request)
    publicacoes = Post.objects.all().filter(usuario=request.user).order_by('-id')
    qnt_acessos = 0
    qnt_comentarios = 0
    qnt_analise = 0
    qnt_curtidas = 0

    for publicacao in publicacoes:
        qnt_acessos += publicacao.acessos
        qnt_comentarios += publicacao.comentarios.count()
        qnt_analise += publicacao.comentarios.filter(aprovado=False).count()
        qnt_curtidas += publicacao.curtidas.count()

    return render(
        request, 
        'professores/geral.html',
        {
            'form': form,
            'publicacoes': publicacoes,
            'qnt_acessos': qnt_acessos,
            'qnt_comentarios': qnt_comentarios,
            'qnt_analise': qnt_analise,
            'qnt_curtidas': qnt_curtidas,
        }
    )

@require_GET
@professor_requerido
def escrever(request):
    form = incluir_feedback(request)
    form_post = PostForm()
    proximo = definir_url_anterior(request)

    return render(request, 'professores/escrever.html', {'form': form, 'form_post': form_post, 'proximo': proximo})

@require_POST
@professor_requerido
def criar_publicacao(request):
    form = PostForm(data=request.POST, files=request.FILES)

    if not form.is_valid():
        erros = form.errors.get_json_data()
        erros = {campo:mensagem[0]['message'] for (campo, mensagem) in erros.items()}

        return JsonResponse({'erros': erros}, status=409)
    else:
        publicacao = form.save()
        url_nova_publicacao = reverse('publicacao', args={publicacao.slug})

        messages.success(request, f'"{ publicacao.titulo }" publicada com sucesso')

        return JsonResponse({'url': url_nova_publicacao}, status=201)

@require_POST
@professor_requerido
def excluir_publicacao(request):
    slug = loads(request.body)['slug']

    try:
        post = Post.objects.get(slug=slug)

        if post.usuario == request.user:
            post.delete()

            return HttpResponse(status=204)
        else:
            return HttpResponse(status=401)
    except ObjectDoesNotExist:
        return HttpResponse(status=409)

@require_GET
@professor_requerido
def alterar_publicacao(request, slug: str):
    publicacao = get_object_or_404(Post, slug=slug)
    proximo = definir_url_anterior(request)

    if publicacao.usuario != request.user:
        messages.error(request, 'Você não pode alterar essa publicação. Não foi você quem a escreveu.')

        return redirect(proximo)

    foto = publicacao.foto.url
    form = incluir_feedback(request)
    form_post = PostForm(instance=publicacao)
    url_salvar = reverse('salvar-publicacao', args={publicacao.slug})

    return render(request, 'professores/alterar.html', {'form': form, 'form_post': form_post, 'foto': foto, 'proximo': proximo, 'url_salvar': url_salvar})

@require_POST
@professor_requerido
def salvar_publicacao(request, slug: str):
    publicacao = get_object_or_404(Post, slug=slug)
    form = PostForm(data=request.POST, files=request.FILES, instance=publicacao)

    if not form.is_valid():
        erros = form.errors.get_json_data()
        erros = {campo:mensagem[0]['message'] for (campo, mensagem) in erros.items()}

        return JsonResponse({'erros': erros}, status=409)
    else:
        publicacao = form.save()
        url_nova_publicacao = reverse('publicacao', args={publicacao.slug})

        messages.success(request, f'"{ publicacao.titulo }" alterada com sucesso')

        return JsonResponse({'url': url_nova_publicacao}, status=200)

@require_POST
@professor_requerido
def aprovar_comentario(request):
    comentario_id = loads(request.body)['comentario_id']

    try:
        comentario = Comentario.objects.get(id=comentario_id)

        comentario.aprovado = True
        comentario.save()
    except Comentario.DoesNotExist:
        return HttpResponse(status=409)

    return HttpResponse(status=200)

@require_POST
@professor_requerido
def deletar_comentario(request):
    comentario_id = loads(request.body)['comentario_id']

    try:
        comentario = Comentario.objects.get(id=comentario_id)
        
        comentario.delete()
    except Comentario.DoesNotExist:
        return HttpResponse(status=409)

    return HttpResponse(status=200)
