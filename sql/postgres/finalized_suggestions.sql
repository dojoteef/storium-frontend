SELECT
  m.name AS model_name,
  s.story->>'game_pid' AS game_pid,
  sg.generated->>'description' AS generated_text,
  sg.finalized->>'description' AS user_text,
  fm.response AS comments,
  ff.response AS fluency,
  fl.response AS likeability,
  fr.response AS relevance,
  fc.response AS coherence
FROM figmentator AS m
  INNER JOIN figmentator_for_story AS ffs
  ON m.id = ffs.model_id

  INNER JOIN suggestion AS sg
  ON sg.story_hash = ffs.story_hash

  INNER JOIN story AS s
  ON sg.story_hash = s.hash

  LEFT OUTER JOIN feedback AS fm
  ON sg.uuid = fm.suggestion_id AND fm.type::text = 'comments'

  LEFT OUTER JOIN feedback AS ff
  ON sg.uuid = ff.suggestion_id AND ff.type::text = 'fluency'

  LEFT OUTER JOIN feedback AS fl
  ON sg.uuid = fl.suggestion_id AND fl.type::text = 'likeability'

  LEFT OUTER JOIN feedback AS fr
  ON sg.uuid = fr.suggestion_id AND fr.type::text = 'relevance'

  LEFT OUTER JOIN feedback AS fc
  ON sg.uuid = fc.suggestion_id AND fc.type::text = 'coherence'
WHERE
  sg.finalized::text != 'null'
  AND :status @> array[m.status]
  AND s.story->>'game_pid' != ALL(:blacklist)
ORDER BY sg.context->>'created_at';
