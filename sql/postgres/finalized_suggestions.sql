SELECT
  m.name AS model_name,
  s.generated->>'description' AS generated_text,
  s.finalized->>'description' AS user_text,
  fm.response AS comments,
  ff.response AS fluency,
  fl.response AS likeability,
  fr.response AS relevance,
  fc.response AS coherence
FROM figmentator AS m
  INNER JOIN figmentator_for_story AS ffs
  ON m.id = ffs.model_id

  INNER JOIN suggestion AS s
  ON s.story_hash = ffs.story_hash

  LEFT OUTER JOIN feedback AS fm
  ON s.uuid = fm.suggestion_id AND fm.type::text = 'comments'

  LEFT OUTER JOIN feedback AS ff
  ON s.uuid = ff.suggestion_id AND ff.type::text = 'fluency'

  LEFT OUTER JOIN feedback AS fl
  ON s.uuid = fl.suggestion_id AND fl.type::text = 'likeability'

  LEFT OUTER JOIN feedback AS fr
  ON s.uuid = fr.suggestion_id AND fr.type::text = 'relevance'

  LEFT OUTER JOIN feedback AS fc
  ON s.uuid = fc.suggestion_id AND fc.type::text = 'coherence'
WHERE
  s.finalized::text != 'null'
  AND m.status != 'inactive'
ORDER BY s.context->>'created_at';
