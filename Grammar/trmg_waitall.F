      subroutine trmg_waitall(ff2g_rbuf, ff2g, srequest, rrequest,
     >     iband_on_pe, nb_on_pe, mpindex_max, nlat,
     >     ilatn_st, nstack, mpdim_on_pe,
     >     mpdim_gl, nb_gr, nb_on_pe_max)
      Use mod_proc_mpi,   only : npes, mypid
      Use mod_spec_mpi,   only : mp_on_pe
#include "mpif.h"      
c
#include "bamparam.h"   << nbands
      complex ff2g_rbuf(nstack,2, mpdim_on_pe, nb_on_pe_max, npes-1)
      complex ff2g     (mpdim_gl, nstack,2, nb_on_pe_max)
      integer srequest(npes-1)
      integer rrequest(npes-1)
      Integer iband_on_pe(nbands,0:npes-1, nb_gr)
      Integer nb_on_pe(0:npes-1, nb_gr)
      Integer mpindex_max(nlat, 0:npes-1)
c
      integer isrc, icount, ierr
      integer statuses(MPI_STATUS_SIZE, npes-1)
c
c     Completing communication
c
      icount = npes - 1
      If ( icount > 0 ) Then
         call MPI_WAITALL(icount, rrequest, statuses, ierr)
      End If
c
c     copy ff2g_rbuf(,,ibpe,isrc) to ff2g(,,ibpe)
c
      do isrc=0,mypid-1
!cdir concur(by=1)
!cdir nodep
         do ibpe = nb_on_pe(mypid, nb_gr), 1, -1
            iband = iband_on_pe(ibpe, mypid, nb_gr)
            ilatn = ilatn_st + iband - 1
!cdir nodep
            do mp = 1, mpindex_max(ilatn, isrc)
               mp_gl = mp_on_pe(mp, isrc)
               do j = 1, 2
                  do i = 1, nstack
                     ff2g(mp_gl, i,j, ibpe)
     >                 = ff2g_rbuf(i,j, mp, ibpe, isrc+1)
                  enddo
               enddo
            enddo
         enddo
!cdir noconcur
      enddo
c
      do isrc=mypid+1,npes-1
!cdir concur(by=1)
!cdir nodep
         do ibpe = nb_on_pe(mypid, nb_gr), 1, -1
            iband = iband_on_pe(ibpe, mypid, nb_gr)
            ilatn = ilatn_st + iband - 1
!cdir nodep
            do mp = 1, mpindex_max(ilatn, isrc)
               mp_gl = mp_on_pe(mp, isrc)
               do j = 1, 2
                  do i = 1, nstack
                     ff2g(mp_gl, i,j, ibpe)
     >                 = ff2g_rbuf(i,j, mp, ibpe, isrc)
                  enddo
               enddo
            enddo
         enddo
!cdir noconcur
      enddo
c
      icount = npes-1
      If ( icount > 0 ) Then
         call MPI_WAITALL(icount, srequest, statuses, ierr)
      End If
c
      return
      end
