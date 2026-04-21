def get_all_builtins(interp):
    registry = {}

    from builtins.string_funcs import register as reg_str
    from builtins.math_funcs import register as reg_math
    from builtins.time_funcs import register as reg_time
    from builtins.file_funcs import register as reg_file
    from builtins.form_funcs import register as reg_form
    from builtins.task_funcs import register as reg_task
    from builtins.map_funcs import register as reg_map
    from builtins.misc_funcs import register as reg_misc
    from builtins.stub_funcs import register as reg_stub

    try:
        from builtins.sql_funcs import register as reg_sql
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
