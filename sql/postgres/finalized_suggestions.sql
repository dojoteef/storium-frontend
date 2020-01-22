SELECT
  m.name AS model_name,
  s.generated->>'description' AS generated_text,
  s.finalized->>'description' AS user_text
FROM figmentator AS m
  INNER JOIN figmentator_for_story AS ffs
  ON m.id = ffs.model_id
    INNER JOIN suggestion AS s
    ON s.story_hash = ffs.story_hash
WHERE s.finalized::text != 'null';
