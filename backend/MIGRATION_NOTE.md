# Database Migration Note

## Embedding Model Change: all-MiniLM-L6-v2

We've switched from Gemini embeddings (768 dimensions) to all-MiniLM-L6-v2 (384 dimensions).

### Required Database Changes

If you have existing data, you need to:

1. **Drop existing embedding data** (if any):
   ```sql
   DELETE FROM document_chunks;
   ```

2. **Update the embedding column dimension**:
   ```sql
   ALTER TABLE document_chunks 
   ALTER COLUMN embedding TYPE vector(384);
   ```

3. **Update the similarity search function**:
   ```sql
   -- The function in schema.sql has been updated to use vector(384)
   -- Run the updated function definition from schema.sql
   ```

4. **Recreate the vector index**:
   ```sql
   DROP INDEX IF EXISTS idx_chunks_embedding;
   CREATE INDEX idx_chunks_embedding ON document_chunks 
   USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```

### For New Installations

Simply run the updated `schema.sql` file - it already includes the correct 384-dimension vectors.

### Benefits of all-MiniLM-L6-v2

- **Faster**: Local processing, no API calls for embeddings
- **Cost-effective**: No embedding API costs
- **Reliable**: No rate limits or API downtime
- **Privacy**: Embeddings generated locally
- **Quality**: Excellent performance for semantic similarity tasks

### Model Details

- **Model**: sentence-transformers/all-MiniLM-L6-v2
- **Dimensions**: 384
- **Max Sequence Length**: 256 tokens
- **Performance**: High quality semantic embeddings
- **Size**: ~90MB model download