SELECT
  f.type,
  m.name AS model_name,
  round(avg(cast(f.response AS int)), 2) AS avg_rating,
  count(m.name) AS feedback_count
FROM figmentator AS m
  INNER JOIN figmentator_for_story AS ffs
  ON m.id = ffs.model_id
    INNER JOIN suggestion AS s
    ON s.story_hash = ffs.story_hash
      INNER JOIN feedback AS f
      ON f.suggestion_id = s.uuid
WHERE
  f.type IN ('fluency', 'likeability', 'relevance', 'coherence')
  AND cast(s.finalized AS text) != 'null'
  AND m.status != 'inactive'
GROUP BY f.type, m.name
ORDER BY f.type, avg_rating DESC;
