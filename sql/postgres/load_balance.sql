WITH
    monthly_totals AS
    (SELECT
       r.id as model_id,
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
        COALESCE(s.timestamp, CURRENT_DATE) > date_trunc('month', CURRENT_DATE)
    GROUP BY
        r.id),
    story_totals AS
    (SELECT
       r.id,
       r.url,
       r.name,
       r.type,
       r.status,
       COUNT(rfs.story_hash) AS story_count
    FROM
        figmentator AS r
            LEFT JOIN
        figmentator_for_story AS rfs
            ON r.id = rfs.model_id
            LEFT JOIN
        monthly_totals AS mt
            ON r.id = mt.model_id
    WHERE
        r.status = 'active'
        AND (r.quota < 0 OR mt.suggestion_count < r.quota)
    GROUP BY
        r.id),
    min_counts AS
    (SELECT
        type,
        MIN(story_count) AS min_count
    FROM
        story_totals
    GROUP BY
        type)
SELECT DISTINCT ON (st.type)
    st.id,
    st.url,
    st.name,
    st.type,
    st.status
FROM
    story_totals AS st
        LEFT JOIN
    min_counts AS mc
        ON mc.type = st.type
WHERE
    st.story_count = mc.min_count
