from django.shortcuts import render
from django.http import JsonResponse
import PyPDF2
import json
from django.views.decorators.csrf import csrf_exempt

from .utils import split_text
from .embeddings import load_embedding_model, embed_texts
from .generation import generate_answer_gemini

embedding_model = load_embedding_model()
docs_chunks = []
docs_embeddings = None

def home(request):
    return render(request, "index.html")

@csrf_exempt
def upload_file(request):
    global docs_chunks, docs_embeddings
    if request.method == 'POST' and request.FILES.getlist('files'):
        try:
            all_chunks = []
            for file in request.FILES.getlist('files'):
                text = ""
                if file.name.endswith('.txt'):
                    text = file.read().decode('utf-8')
                elif file.name.endswith('.pdf'):
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = "\n".join([page.extract_text() or "" for page in pdf_reader.pages])

                if text:
                    chunks = split_text(text)
                    all_chunks.extend(chunks)

            if all_chunks:
                docs_chunks = all_chunks
                docs_embeddings = embed_texts(all_chunks, embedding_model)
                return JsonResponse({"status": "success", "chunks": len(all_chunks)})

            return JsonResponse({"status": "error", "message": "File was empty or unreadable"})

        except Exception as e:
            import traceback
            traceback.print_exc()  # logs error in console
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "No file uploaded"})

@csrf_exempt
def chat(request):
    global docs_chunks
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

        query = data.get("query", "").strip()
        if not query:
            return JsonResponse({"status": "error", "message": "Empty query"}, status=400)
        if not docs_chunks:
            return JsonResponse({"status": "error", "message": "No documents uploaded"}, status=400)

        # ✅ Naive retrieval (later replace with similarity search)
        context = " ".join(docs_chunks[:5])

        try:
            answer = generate_answer_gemini(query, context)
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Generation failed: {str(e)}"}, status=500)

        return JsonResponse({"status": "success", "answer": answer})

    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)
