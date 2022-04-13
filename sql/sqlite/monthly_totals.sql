SELECT
    COALESCE(COUNT(s.story_hash), 0) AS suggestion_count
FROM
    figmentator AS r
        LEFT OUTER JOIN
    figmentator_for_story AS rfs
        ON r.id = rfs.model_id
        LEFT JOIN
    suggestion AS s
        ON rfs.story_hash = s.story_hash
WHERE
    r.id = :model_id
    AND COALESCE(s.timestamp, date('now')) > date('now', 'start of month')
GROUP BY
    r.id
