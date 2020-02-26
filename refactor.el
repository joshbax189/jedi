;; Test implementations of refactorings

(defvar jedi-output-buffer "*Test output*")

;; Extract
(defun jedi-extract (name start end)
  (interactive "sName:\nr")
  ;; start a python interpreter
  (let ((end-line (number-to-string (line-number-at-pos)))
        (end-col (number-to-string (current-column))))

    (exchange-point-and-mark)

    (let* ((start-line (number-to-string (line-number-at-pos)))
          (start-col (number-to-string (current-column)))
          (command (concat "print(jedi.refactoring.extract(jedi.Script(path='" (buffer-file-name) "'), '" name
                           "', line=" start-line
                           ", column=" start-col
                           ", end_line=" end-line
                           ", end_column=" end-col
                           ").diff())")))
      (shell-command (concat "python -c \"import jedi; import jedi.refactoring; " command "\"") jedi-output-buffer)
      (with-current-buffer jedi-output-buffer
        (diff-mode)))
    (exchange-point-and-mark))
  )

;; Rename
(defun jedi-rename (name start end)
  (interactive "sName:\nr")
  ;; start a python interpreter
  (let ((command (concat "print(jedi.refactoring.rename(jedi.Script(path='" (buffer-file-name) "'), '" name "', line=" (number-to-string (line-number-at-pos))
                        ", column=" (number-to-string (current-column)) ").diff())")))
    (shell-command (concat "python -c \"import jedi; import jedi.refactoring; " command "\"") jedi-output-buffer)
    (with-current-buffer jedi-output-buffer
      (diff-mode)))
  )

;; Inline
(defun jedi-inline ()
  (interactive)
  ;; start a python interpreter
  (let ((command (concat "print(jedi.refactoring.inline(jedi.Script(path='" (buffer-file-name) "'), line=" (number-to-string (line-number-at-pos))
                        ", column=" (number-to-string (current-column)) ").diff())")))
    (shell-command (concat "python -c \"import jedi; import jedi.refactoring; " command "\"") jedi-output-buffer)
    (with-current-buffer jedi-output-buffer
      (diff-mode)))
  )
