      subroutine test
      integer i,j,k
      dimension a(100)

      a(1:2:3) = 5
      print *,(1,2)
      print *,(1+2*3)
      print *,(i,i=1,3)
      print *,(i,i+1,i=1,3)
      print *,((i,j,j=1,3),(k,i,k=1,3),i=1,3)
      print *,((j+1,j+2,j+i,j=1,3),i,i+1,i+2, i=1, 6)
      if (a.eq.b) then 
         x=2
         y=3
      endif
      end
