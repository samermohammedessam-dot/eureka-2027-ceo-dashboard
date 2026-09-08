/** Pass filters.page to get { records, total, page, pageSize, totalPages } instead of a plain array — see paginate_(). */
function api_getTasks(filters) {
  return safeCall_(function () {
    var tStart = new Date().getTime();
    var all = applyFilters_(readAllRecords(SHEETS.TASKS).map(stripRowMeta_), filters);
    var result = (filters && filters.page) ? paginate_(all, filters) : all;
    logTiming_('api_getTasks', new Date().getTime() - tStart);
    return result;
  });
}

function api_saveTask(task) {
  return safeCall_(function () {
    if (task.taskId) {
      updateRecordById(SHEETS.TASKS, task.taskId, task);
    } else {
      task.status = task.status || 'Not Started';
      task.percentCompletion = task.percentCompletion || 0;
      appendRecord(SHEETS.TASKS, task);
    }
    recomputeTasks_();
    invalidateDashboardCache_();
    return task.taskId || true;
  });
}

function api_deleteTask(taskId) {
  return safeCall_(function () {
    var result = deleteRecordById(SHEETS.TASKS, taskId);
    invalidateDashboardCache_();
    return result;
  });
}
