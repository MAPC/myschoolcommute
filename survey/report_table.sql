CREATE VIEW survey_child_survey AS
SELECT
    c.id, c.grade, c.to_school, c.dropoff, c.from_school, c.pickup,
    s.school_id, s.street, s.cross_st, s.nr_vehicles, s.nr_licenses, s.distance, s.created, s.modified,
    st_astext(s.location),
    trunc(log(2, (ST_Intersects(sch.shed_20, ST_Transform(geometry(s.location),26986))::int::bit ||
    ST_Intersects(sch.shed_15, ST_Transform(geometry(s.location),26986))::int::bit ||
    ST_Intersects(sch.shed_10, ST_Transform(geometry(s.location),26986))::int::bit ||
    ST_Intersects(sch.shed_05, ST_Transform(geometry(s.location),26986))::int::bit || 1::int::bit)::bit(5)::int)) AS shed,
    now() as current_time
FROM survey_child as c
LEFT JOIN survey_survey as s
ON c.survey_id = s.id
LEFT JOIN survey_school as sch
ON s.school_id = sch.id;