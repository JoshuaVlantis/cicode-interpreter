def get_all_builtins(interp):
    registry = {}

    from cibuiltins.string_funcs import register as reg_str
    from cibuiltins.math_funcs import register as reg_math
    from cibuiltins.time_funcs import register as reg_time
    from cibuiltins.file_funcs import register as reg_file
    from cibuiltins.form_funcs import register as reg_form
    from cibuiltins.task_funcs import register as reg_task
    from cibuiltins.map_funcs import register as reg_map
    from cibuiltins.misc_funcs import register as reg_misc
    from cibuiltins.stub_funcs import register as reg_stub

    try:
        from cibuiltins.sql_funcs import register as reg_sql
        reg_sql(registry, interp)
    except ImportError:
        pass

    reg_str(registry, interp)
    reg_math(registry, interp)
    reg_time(registry, interp)
    reg_file(registry, interp)
    reg_form(registry, interp)
    reg_task(registry, interp)
    reg_map(registry, interp)
    reg_misc(registry, interp)
    reg_stub(registry, interp)

    return registry
