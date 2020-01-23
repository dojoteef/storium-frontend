WITH
  suggestion_counts AS
  (
    SELECT
      count(json_extract(context, '$.user_pid')) AS suggestion_count
    FROM suggestion
    GROUP BY json_extract(context, '$.user_pid')
  )
  SELECT
    count(suggestion_count) AS unique_user_count
  FROM suggestion_counts
  WHERE suggestion_count < :suggestion_count;
