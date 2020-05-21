SELECT
  context.suggestion_id AS suggestion_id,
  context.model_name AS model_name,
  context.story AS story,
  context.generated AS generated,
  context.finalized AS finalized
FROM (
  SELECT
    sg.id AS suggestion_id,
    m.name AS model_name,
    s.story AS story,
    sg.generated AS generated,
    sg.finalized AS finalized,
    ROW_NUMBER() OVER (PARTITION BY m.name ORDER BY sg.id ASC) AS rno
  FROM figmentator AS m
    INNER JOIN figmentator_for_story AS ffs
    ON m.id = ffs.model_id

    INNER JOIN suggestion AS sg
    ON sg.story_hash = ffs.story_hash

    INNER JOIN story AS s
    ON sg.story_hash = s.hash

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
    AND m.status != 'inactive'
    AND s.story->>'game_pid' != ALL(:blacklist)
    AND ff.response IS NOT NULL
    AND fl.response IS NOT NULL
    AND fr.response IS NOT NULL
    AND fc.response IS NOT NULL
  ORDER BY sg.id
) AS context
WHERE context.rno::FLOAT4 <= :limit
ORDER BY context.model_name;
