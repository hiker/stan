C @(#) $Source$
C @(#) $Name$ $Revision: 3 $ $Date: 2003-06-30 12:50:24 +1000 (Mon, 30 Jun 2003) $
      program GAM
#include "globalerr.h"  << GLOBALERRFLAG
C JH Dummy test
      integer :: i,j
      if(1.eq.2) print *,"1"
      x= 1.e2**2
      y => x
c
      GLOBALERRFLAG = 0
C    timing
!cdir nodep
      call xxinit
      call xxts(1)
      call gaminit
C    timing
      call xxte(1)
c
C    timing
      call xxts(2)
      call gamloop ( 0 )
C    timing
      call xxte(2)
      print *,"Exit GAMLOOP"
c
C    timing
      call xxts(3)
      call gamend
C    timing
      call xxte(3)
 
      do i=1,16
      call xxtfin
      enddo
      call xxtprt
c
      if ( GLOBALERRFLAG .gt. 0 ) then
         call abstop
      else
      stop
      endif
      stop

c+.........................................................................
c+..  cvs source code maintenance note:              azs ( 7th August 2001)  
c+..                                               
c+..  bam3-0                                       
c+..                                               
c+..  Make this routine the new marker routine for convenient tracking
c+..  of cvs logs entered with major "commit" of new revision.
c+..  From revision "mar2001" onwards, gam.F is the main program for 
c+..  both gam (gasp) and agcm. See cvs docs available from repository
c+..  "bam/doc/*.txt" for more information on the series of major but
c+..   unofficial revisions leading from bam2c5 to bam3-0
c+..
c+..  Thu 28 June 2001:           check-in bam_longv.
c+..  Fri 29 June 2001:           check-in bam_vbucket.
c+..                              check-in bam_bluerk.
c+..                              check-in bam_mar2001.
c+..
c+..  Mon/Tue, 30/31 July 2001:   completed bam_mar2001 check-in.
c+..                              check-in bam_uv.
c+..  Wed 1st August 2001:        check-in bam_xray.
c+..  Mon 6th August 2001:        check-in bam_gamma
c+..                              check-in bam_cosmic
c+..  Tue 7th August 2001:        update bam_3-0    
c+..              
c+.........................................................................

      end
