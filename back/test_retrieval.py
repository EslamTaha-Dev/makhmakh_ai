from app.services.retrieval import search_similar_chunks


course_id = "338c62c4-596e-43df-9ec3-028f13d9f09c"

results = search_similar_chunks(
    course_id=course_id,
    query="What is the main concept discussed in this course?",
    top_k=5,
)

for result in results:
    print("=" * 80)
    print("FILE:", result["file_name"])
    print("DISTANCE:", result["distance"])
    print(result["text"])