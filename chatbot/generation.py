import google.generativeai as genai
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def configure_gemini():
    """
    Configure Gemini API with the key from Django settings (loaded from environment).
    """
    api_key = getattr(settings, "GENAI_API_KEY", None)
    if not api_key:
        raise ImproperlyConfigured("❌ Missing GENAI_API_KEY in settings or environment.")
    genai.configure(api_key=api_key)


def generate_answer_gemini(context: str, query: str) -> str:
    """
    Generate an answer using the Gemini API with given context and query.
    """
    try:
        configure_gemini()
        model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
        prompt = f"""
        You are a helpful assistant that answers questions based on the provided document context.

        Context:
        {context}

        Question: {query}
        Answer:"""
        response = model.generate_content(prompt)
        return response.text.strip() if response and response.text else "⚠️ No response generated."
    except Exception as e:
        return f"Error generating response: {str(e)}"


def generate_answer_fallback(context: str, query: str) -> str:
    """
    Simple fallback if Gemini API fails.
    """
    return f"Simulated answer based on retrieved content:\n\n{context[:1000]}..."
