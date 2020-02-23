WITH
  suggestion_counts AS
  (
    SELECT
      count(json_extract(context, '$.user_pid')) AS suggestion_count
    FROM suggestion
      INNER JOIN figmentator_for_story AS ffs
      ON sg.story_hash = ffs.story_hash
        INNER JOIN figmentator AS m
        ON ffs.model_id = m.id
    WHERE m.status != 'inactive'
    GROUP BY json_extract(context, '$.user_pid')
  )
  SELECT
    count(suggestion_count) AS unique_user_count
  FROM suggestion_counts
  WHERE suggestion_count <= :suggestion_count;
