WITH
  suggestion_counts AS
  (
    SELECT DISTINCT ON (context->>'user_pid')
      count(context->>'user_pid') AS suggestion_count
    FROM suggestion
    GROUP BY context->>'user_pid'
  )
  SELECT
    count(suggestion_count) AS unique_user_count
  FROM suggestion_counts
  WHERE suggestion_count::FLOAT4 <= :suggestion_count;
