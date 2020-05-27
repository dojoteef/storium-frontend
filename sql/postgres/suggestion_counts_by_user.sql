WITH
  suggestion_counts AS
  (
    SELECT DISTINCT ON (context->>'user_pid')
      count(context->>'user_pid') AS suggestion_count
    FROM suggestion AS sg
      INNER JOIN figmentator_for_story AS ffs
      ON sg.story_hash = ffs.story_hash
        INNER JOIN figmentator AS m
        ON ffs.model_id = m.id
    WHERE :status @> array[m.status]
    GROUP BY context->>'user_pid'
  )
  SELECT
    count(suggestion_count) AS unique_user_count
  FROM suggestion_counts
  WHERE suggestion_count::FLOAT4 <= :suggestion_count;
