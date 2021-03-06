SELECT
  m.name AS model_name,
  json_extract(s.generated, '$.description') AS generated_text,
  json_extract(s.finalized, '$.description') AS user_text,
  f.response AS comments
FROM figmentator AS m
  INNER JOIN figmentator_for_story AS ffs
  ON m.id = ffs.model_id
    INNER JOIN suggestion AS s
    ON s.story_hash = ffs.story_hash
      LEFT OUTER JOIN feedback AS f
      ON s.uuid = f.suggestion_id AND f.type = 'comments'
WHERE
  cast(json_extract(s.finalized, '$.description') AS text) != 'null'
  AND m.status != 'inactive'
ORDER BY json_extract(s.context, '$.created_at');
