      subroutine trgm_waitall(workf2m_rbuf, workf2m,
     >     srequest, rrequest,
     >     iband_on_pe, nb_on_pe,
     >     nstack2, mpdim_on_pe, mbands_gl, nb_gr, nb_on_pe_max)
c
      Use mod_proc_mpi,   only : mypid, npes
#include "mpif.h"
c
      complex workf2m_rbuf (nstack2,2,mpdim_on_pe,nb_on_pe_max,npes-1)
      complex workf2m      (mpdim_on_pe, nstack2, 2, mbands_gl)
c
      integer srequest(npes-1)
      integer rrequest(npes-1)
#include "bamparam.h"   << nbands
      Integer iband_on_pe(nbands,0:npes-1, nb_gr)
      Integer nb_on_pe(0:npes-1, nb_gr)
c
      integer status(MPI_STATUS_SIZE)
      integer statuses(MPI_STATUS_SIZE, npes-1)
c
c     Completes receives
c
      icount = npes-1
!cdir pardo, nobarr=(entry,exit)
      do i=1, npes-1
!cdir critical
         call MPI_Waitany(icount,rrequest, indx, status, ierr)
! Adjust the index in the rrequest array to the src rank
         if (indx .le. mypid) indx=indx-1
         print *,"Iteration",i,"received indx",indx
!cdir endcritical
c
!cdir nodep
         do ibpe=nb_on_pe(indx,nb_gr), 1, -1
            iband = iband_on_pe(ibpe,indx,nb_gr)
            do i3=1,2
               do i2=1,nstack2
                 do i1=1,mpdim_on_pe
                     workf2m(i1,i2,i3,iband)
     >                    = workf2m_rbuf(i2,i3,i1,ibpe,indx+1)
                  enddo !i1
               enddo !i2
            enddo !i3
         enddo !ibpe
      enddo
c
!cdir serial
      icount=npes-1
      If ( icount > 0 ) Then
         call MPI_WAITALL(icount, srequest, statuses, ierr)
      End If
!cdir endserial
      return
      end
