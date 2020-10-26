tool_name = 'Renderer'
report_type = 'ec'
show_skipped_groups = True
tracked_metrics = {
    'gpu_memory_max': {'name': 'GPU memory max', 'function': 'avrg', 'displaying_unit': 'Mb'}, 
    'gpu_memory_total': {'name': 'GPU memory total', 'function': 'avrg', 'displaying_unit': 'Mb'}, 
    'gpu_memory_usage': {'name': 'GPU memory usage', 'function': 'avrg', 'displaying_unit': 'Mb'}, 
    'system_memory_usage': {'name': 'System memory usage', 'function': 'avrg', 'displaying_unit': 'Mb'}, 
    'render_time': {'name': 'Render time', 'function': 'sum', 'displaying_unit': 's'}
}
tracked_metrics_files_number = 10