SELECT
  sg.id as suggestion_id,
  m.name AS model_name,
  s.story AS story,
  sg.generated AS generated
FROM figmentator AS m
  INNER JOIN figmentator_for_story AS ffs
  ON m.id = ffs.model_id

  INNER JOIN suggestion AS sg
  ON sg.story_hash = ffs.story_hash

  INNER JOIN story AS s
  ON sg.story_hash = s.hash
WHERE
  sg.finalized::text != 'null'
  AND m.status != 'inactive'
  AND s.story->>'game_pid' != ALL(:blacklist)
ORDER BY sg.context->>'created_at';
