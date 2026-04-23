DEFINE EVENT OVERWRITE file_deleted ON file
    WHEN $event = 'DELETE'
    THEN {
        DELETE chunk WHERE doc = $before.id;
        DELETE keyword WHERE (<-REL_FILE_HAS_KEYWORD).len() = 0;
    };
