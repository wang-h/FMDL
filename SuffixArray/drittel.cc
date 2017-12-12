#include <iostream>
#include <stdlib.h>
using namespace std;
#include <Python.h>

#define int Py_ssize_t

inline bool leq(int a1, int a2,   int b1, int b2) { // lexic. order for pairs
  return(a1 < b1 || (a1 == b1 && a2 <= b2));
}                                                   // and triples
inline bool leq(int a1, int a2, int a3,   int b1, int b2, int b3) {
  return(a1 < b1 || (a1 == b1 && leq(a2,a3, b2,b3)));
}
// stably sort a[0..n-1] to b[0..n-1] with keys in 0..K from r
static void radixPass(int* a, int* b, int* r, int n, int K) 
{ // count occurrences
  int* c = new int[K + 1];                          // counter array
  for (int i = 0;  i <= K;  i++) c[i] = 0;         // reset counters
  for (int i = 0;  i < n;  i++) c[r[a[i]]]++;    // count occurences
  for (int i = 0, sum = 0;  i <= K;  i++) { // exclusive prefix sums
     int t = c[i];  c[i] = sum;  sum += t;
  }
  for (int i = 0;  i < n;  i++) b[c[r[a[i]]]++] = a[i];      // sort
  delete [] c;
}

// find the suffix array SA of s[0..n-1] in {1..K}^n
// require s[n]=s[n+1]=s[n+2]=0, n>=2
void suffixArray(int* s, int* SA, int n, int K) {
  int n0=(n+2)/3, n1=(n+1)/3, n2=n/3, n02=n0+n2; 
  int* s12  = new int[n02 + 3];  s12[n02]= s12[n02+1]= s12[n02+2]=0; 
  int* SA12 = new int[n02 + 3]; SA12[n02]=SA12[n02+1]=SA12[n02+2]=0;
  int* s0   = new int[n0];
  int* SA0  = new int[n0];
 
  // generate positions of mod 1 and mod  2 suffixes
  // the "+(n0-n1)" adds a dummy mod 1 suffix if n%3 == 1
  for (int i=0, j=0;  i < n+(n0-n1);  i++) if (i%3 != 0) s12[j++] = i;

  // lsb radix sort the mod 1 and mod 2 triples
  radixPass(s12 , SA12, s+2, n02, K);
  radixPass(SA12, s12 , s+1, n02, K);  
  radixPass(s12 , SA12, s  , n02, K);

  // find lexicographic names of triples
  int name = 0, c0 = -1, c1 = -1, c2 = -1;
  for (int i = 0;  i < n02;  i++) {
    if (s[SA12[i]] != c0 || s[SA12[i]+1] != c1 || s[SA12[i]+2] != c2) { 
      name++;  c0 = s[SA12[i]];  c1 = s[SA12[i]+1];  c2 = s[SA12[i]+2];
    }
    if (SA12[i] % 3 == 1) { s12[SA12[i]/3]      = name; } // left half
    else                  { s12[SA12[i]/3 + n0] = name; } // right half
  }

  // recurse if names are not yet unique
  if (name < n02) {
    suffixArray(s12, SA12, n02, name);
    // store unique names in s12 using the suffix array 
    for (int i = 0;  i < n02;  i++) s12[SA12[i]] = i + 1;
  } else // generate the suffix array of s12 directly
    for (int i = 0;  i < n02;  i++) SA12[s12[i] - 1] = i; 

  // stably sort the mod 0 suffixes from SA12 by their first character
  for (int i=0, j=0;  i < n02;  i++) if (SA12[i] < n0) s0[j++] = 3*SA12[i];
  radixPass(s0, SA0, s, n0, K);

  // merge sorted SA0 suffixes and sorted SA12 suffixes
  for (int p=0,  t=n0-n1,  k=0;  k < n;  k++) {
#define GetI() (SA12[t] < n0 ? SA12[t] * 3 + 1 : (SA12[t] - n0) * 3 + 2)
    int i = GetI(); // pos of current offset 12 suffix
    int j = SA0[p]; // pos of current offset 0  suffix
    if (SA12[t] < n0 ? 
        leq(s[i],       s12[SA12[t] + n0], s[j],       s12[j/3]) :
        leq(s[i],s[i+1],s12[SA12[t]-n0+1], s[j],s[j+1],s12[j/3+n0]))
    { // suffix from SA12 is smaller
      SA[k] = i;  t++;
      if (t == n02) { // done --- only SA0 suffixes left
        for (k++;  p < n0;  p++, k++) SA[k] = SA0[p];
      }
    } else { 
      SA[k] = j;  p++; 
      if (p == n0)  { // done --- only SA12 suffixes left
        for (k++;  t < n02;  t++, k++) SA[k] = GetI(); 
      }
    }  
  } 
  delete [] s12; delete [] SA12; delete [] SA0; delete [] s0; 
}

// Added by Yves Lepage to compute LCP.

// compute the longest common prefixes of s[0..n-1] with suffix array SA
// Linear computation of LCP (algorithm GetHeight) from paper
// Toru Kasai et al., Linear-Time Longest-Common-Prefix Computation in Sux Arrays and Its Applications
// A. Amir and G.M. Landau (Eds.): CPM 2001, LNCS 2089, pp. 181--192, Springer 2001.
// See also: slide 166 in http://www.cs.helsinki.fi/u/tpkarkka/opetus/11s/spa/lecture10.pdf
// Is there a bug in both version?
// See two modifications hereafter to get exact result...
void longestCommonPrefixes(int* ss, int* SA, int *lcp, int n)
{
	// Create the inverse array of SA.
	// We should not forget to clean up before leaving.
	int *rank = new int[n] ;
	
	// Initialize inverse array of SA: rank[i] = k <=> k = SA[i].
    for ( int i = 0 ;  i < n ;  ++i )
		rank[SA[i]] = i ;
		
	// Main loop.
	// In the worst case, because h decreases,
	// the number of times the inner loop is executed is 2n.
	// h is the height.
    for ( int i = 0, h = 0 ;  i < n ;  ++i )
	{
		int ranki = rank[i] ;

		// Add the following verification to algorithm of paper.
		if ( 0 < h-1 )
			h = h-1 ;
		else
			h = 0 ;
		// End of addition.
		if ( ranki > 0 )
		{
			int j = SA[ranki-1] ;
			// Add more verification than given in algorithm of quoted paper.
			// In the quoted paper: while ( ss[i+h] == ss[j+h] )
			while ( (i+h < n) && (j+h < n) && (ss[i+h] == ss[j+h]) )
			{
				h += 1 ;
			} ;
			lcp[ranki] = h ;
		}
		else
		{
			h = 0 ;
		} ;
	} ;
	
	// The first element in SA does not have any predecessor,
	// hence, we set the value of its lcp to an impossible value.
	lcp[0] = -1 ;
	
	// Clean up to avoid leaking.
	delete [] rank ;
}

// Added by Yves Lepage for interface with Python

// Input s: an array of integers (*** not an array of characters ***)
// Output: result, the suffix array for s.
void suffix_array(PyObject *s, PyObject *saresult, PyObject  *lcpresult)
{
	int n = 0 ;
	int K = 0 ;
	
	// Determine the length of the array of integers.
	n = (int) PyList_Size(s) ;
	// cout << "len(s) = " << n << "\n" ;

	// Create C++ arrays for the array of integers and the suffix array.
	// We should remember to delete these arrays before leaving.
    int* ss = new int[n+3] ;
    int* SA = new int[n+3] ;
    int* lcp = new int[n+3] ;
	
	// Copy integers of s (Python object) into ss (C++ integer array).
	// Initialize SA with 1 values.
	// Determine the highest value among integers in s.
	for ( int i = 0 ; i < n ; ++i )
	{
		int val = PyLong_AsLong(PyList_GetItem(s, i)) ;
		if ( K < val ) K = val ;
		ss[i] = val ;
		// cout << "ss[" << i << "] = " << ss[i] << "\n" ;
		SA[i] = 1 ;
		lcp[i] = i ;
    } ;

	// Trick for Kärkkäinen and Sanders algorithm:
	// Add three cells at the end of the array
	// so as to be always able to divide the arrays into three thirds.
	ss[n] = ss[n+1] = ss[n+2] = SA[n] = SA[n+1] = SA[n+2] = 0 ;

	// Call Kärkkäinen and Sanders procedure.
	suffixArray(ss, SA, n, K) ;
	
	// Call longest common prefix procedure.
	longestCommonPrefixes(ss, SA, lcp, n) ;
	
	// Copy suffix array in C++ into a Python list of integers
	// returned by the second and third arguments of the function.
	// These arguments should have been initialized to the exact length
	// before calling this function.
    for ( int i = 0 ; i < n ; ++i )
	{
		// cout << "SA[" << i << "] = " << SA[i] << ", lcp = " << lcp[i] << "\n" ;
		PyList_SetItem(saresult, i, PyLong_FromLong(SA[i]));
		PyList_SetItem(lcpresult, i, PyLong_FromLong(lcp[i]));
	} ;

	// Clean up to avoid leaking.
	delete [] ss ;
	delete [] SA ;
	delete [] lcp ;
}

// The following function should be used only for strings of ASCII characters.
void suffix_array_for_ascii_string(char *s, PyObject *result)
{
	int n = 0 ; // Length of the string of chararcters s
	int K = 0 ; // Highest ord(c) for c in s
	
	// Find K, the highest integer representing a character
	// Important for radix sort.
	for ( char *sz = s ; *sz ; ++sz, ++n )
		if ( K < *sz ) K = *sz ;
		
	// Create C++ arrays for the string and the suffix array.
	// We should remember to delete these arrays before leaving.
    int* ss = new int[n+3] ;
    int* SA = new int[n+3] ;
	
	// Copy characters of s as integers into ss.
	// Initialize SA with 1 values.
    for ( int i = 0 ;  i < n ;  ++i )
	{
		ss[i] = s[i] ;
		SA[i] = 1 ;
    } ;

	// Trick for Kärkkäinen and Sanders algorithm:
	// Add three cells at the end of the array
	// so as to be always able to divide the arrays into three thirds.
	ss[n] = ss[n+1] = ss[n+2] = SA[n] = SA[n+1] = SA[n+2] = 0 ;
	
	// Call Kärkkäinen and Sanders procedure.
	suffixArray(ss, SA, n, K) ;
	
	// Copy suffix array in C into a Python list of integers
	// returned by the second argument of the function.
	// This argument should have been initialized to the exact length
	// before calling this function.
	PyObject *item ;
    for ( int i = 0 ; i < n ; ++i )
	{
		item = PyLong_FromLong(SA[i]);
		// cout << "SA[" << i << "] = " << SA[i] << "\n" ;
		PyList_SetItem(result, i, item);
	} ;

	// Clean up to avoid leaking.
	delete [] ss ;
	delete [] SA ;
}

