
# -1 out a layer, 0 in a layer and 1 no change
_log_indent = 1
def log(_string = '', _indent = 0):
    global _log_indent
    if _indent < 0:
        _log_indent += _indent
    if _string != '':
        print((' |' * _log_indent) + ': ' + _string)
    if _indent > 0:
        _log_indent += _indent