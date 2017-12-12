/* File: drittel.h */

/*
 * Build a suffix array for the string passed as argument
 * input:
 *    one string of type char *
 * output:
 *    an array of integers of type int *
 */

void suffix_array(PyObject *s, PyObject *sa, PyObject *lcp) ; /* build suffix array for s */
void suffix_array_for_ascii_string(char *s, PyObject *sa) ; /* build suffix array for s */
