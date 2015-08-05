# stan
A Fortran Static Analyzer

The idea of this library is to enable users to write their own
tool to handle Fortran source files. Some examples:

- Reformat a Fortran file
  For example have all keywords upper case, all variables lower case.

- Add implicit none (and all missing variables declations to a source file).

- Study code in maths mode, e.g.:
```
      DO j = 1, veg_pts
         l = veg_index(j)
                             o3mol(l)
         flux_o3(l) =  -------------------- 
                                ratio_o3
                        ra(l)+ ---------- 
                                 gl(l)
         rd(l) = rd(l)*fo3(l)
      END DO

                           +-----------+
      fo3(l) = -0.5*b+0.5*\| b*b-4.0*c

                            +-----------------------------+
                -b2(l)      |   b2(l) * b2(l)     b3(l)   |
      wp(l) =  --------- -\ |  --------------- - ------- 
                2*b1(l)    \|   4*b1(l)*b1(l)     b1(l)


                                                                                                                                          0.8
                                                                                                          km_dsct_factor(i,j) * z_pr
                                            0.75 * rho_tq(i,j,k-1) * v_top_dsc(i,j) * g1 * vkman * ((1.0- ---------------------------- )^    ) * z_pr * z_pr
                                                                                                                     zh_pr
      rhokm_top(i,j,k) = rhokm_top(i,j,k)+ ------------------------------------------------------------------------------------------------------------------ 
                                                                                                 zh_pr
```
- Automatically modify a subroutine so that it will write all input variables at the beginning and
  all output variables at the end into a file. Then create a driver which reads the input data,
  calls the subroutine, and compares the result. This can be used for example to unit testing, or
  help in optimising subroutines.

At this stage this is pretty much work in progress, but e.g. maths mode already works:
```
PYTHONPATH=. bin/MathsMode.py my_fortran_file.F90
```