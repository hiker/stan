      subroutine test
      real :: a, b, c, d
!      a = a+x*(x / y)
!      a = ((b+c)*b)/(c+d)/x * y + x
!      a = ((b+c)*b)/(c+d)/x * y/x + x
      a = ((b+c)*b)/(c+d)/x * (y/x) + x
      a = 2-(b+c)*b/(c+d)
!      a = a/(b/c+d)
!      a = exp(exp(a))
!      a = x**y
!      a = (b*x/x)**(d*e/h)
      a = sqrt( (a**2 + b**2) )
      a = abs((b*x/x)**(d*e/h))
      end
