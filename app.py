from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from rag.retriever import RAGRetriever

app = Flask(__name__)
CORS(app)

retriever = RAGRetriever()

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "Question is required"}), 400

    answer, docs = retriever.generate_response(question)
    sources = retriever.get_sources(docs)

    return jsonify({"answer": answer, "sources": sources})


if __name__ == "__main__":
    port = 5000
    app.run(host="0.0.0.0", port=port, debug=True)
