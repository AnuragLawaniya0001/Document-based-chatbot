from django.shortcuts import render
from django.http import JsonResponse
import PyPDF2
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from django.views.decorators.http import require_POST
import json

from .utils import split_text
from .embeddings import load_embedding_model, embed_texts
from .generation import generate_answer_gemini 

embedding_model = load_embedding_model()
docs_chunks = []
docs_embeddings = None

def home(request):
    return render(request, 'index.html')

def upload_file(request):
    global docs_chunks, docs_embeddings
    if request.method == 'POST' and request.FILES.getlist('files'):
        all_chunks = []
        for file in request.FILES.getlist('files'):
            text = ""
            if file.name.endswith('.txt'):
                text = file.read().decode('utf-8')
            elif file.name.endswith('.pdf'):
                pdf_reader = PyPDF2.PdfReader(file)
                text = "\n".join([page.extract_text() for page in pdf_reader.pages])
            
            if text:
                chunks = split_text(text)
                all_chunks.extend(chunks)

        if all_chunks:
            docs_chunks = all_chunks
            docs_embeddings = embed_texts(all_chunks, embedding_model)
            return JsonResponse({"status": "success", "chunks": len(all_chunks)})

    return JsonResponse({"status": "error", "message": "No file uploaded"})

def chat(request):
    global docs_chunks
    if request.method == "POST":
        data = json.loads(request.body)
        query = data.get("query", "")

        if not query or not docs_chunks:
            return JsonResponse({"status": "error", "message": "No documents or query provided"})

        # ✅ Pick top chunk (naive retrieval)
        context = " ".join(docs_chunks[:5])  # later can add similarity search

        # ✅ Get answer from Gemini
        answer = generate_answer_gemini(query, context)

        return JsonResponse({"status": "success", "answer": answer})

    return JsonResponse({"status": "error", "message": "Invalid request"})