function api_getTasks(filters) {
  return safeCall_(function () {
    return applyFilters_(readAllRecords(SHEETS.TASKS).map(stripRowMeta_), filters);
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
    return task.taskId || true;
  });
}

function api_deleteTask(taskId) {
  return safeCall_(function () { return deleteRecordById(SHEETS.TASKS, taskId); });
}
