C @(#) $Source$
C @(#) $Name$ $Revision: 3 $ $Date: 2003-06-30 12:50:24 +1000 (Mon, 30 Jun 2003) $
      SUBROUTINE ZERORAD(nlon,nlat)
C***********************************************************************
C.....Routine to zero the DGCFLD fields at appropriate timestep        *
C     Zeroing is controlled by the MASKAC3 settings                    *
C                                                                      *
C     INPUT:                                                           *
C        ALBDAC   - ACCUMULATED SURFACE ALBEDO FIELD                   *
C        DGCFLD   - DIAGNOSTIC CLOUD AND RADIATION FIELDS              *
C        DELT     - TIMESTEP INTERVAL (SECONDS)                        *
C        KOUNT    - CURRENT TIMESTEP                                   *
C        KOUNTR   - NO OF TIMESTEPS BETWEEN RADIATION CALCULATION      *
C        MASKAC3  - ACCUMULATION TYPE MASK                             *
C        NANKNT   - ????                                               *
C        NPREC    - FREQUENCY OF RESETTING ACCUMULATED FIELDS          *
C                                                                      *
C     OUTPUT:                                                          *
C        ALBDAC   - ZEROED                                             *
C        DGCFLD   - ZEROED                                             *
C                                                                      *
C NOTE: SFCFLX(,,,) ARE ZEROED IN ZEROSFGH                             *
C                                                                      *
C***********************************************************************
C   BAMPARAM NEEDED FOR JF,JG2,JS
#include "modeltype.h" << modeltype
#include "bamparam.h"
#include "grid_phy.h"   << nlat_phy, nlon_phy
C   APRADDCB NEEDED FOR KOUNTR
#include "apraddcb.h"
C   AGCONDIT NEEDED FOR KOUNT AND DELT
#include "agcondit.h"
C   AGRTUSE NEEDED FOR NANKNT
#include "agrtuse.h"
C   AGCDTA NEEDED FOR NPREC
#include "agcdta.h"
C   DGCLD NEEDED FOR DGCFLD AND MASKAC3
#include "dgcld.h"
c      INTEGER IDGCFLD(JF,JG2,MAXCLD)
c      EQUIVALENCE (DGCFLD(1,1,1),IDGCFLD(1,1,1))
C   BMGRDBUF NEEDED FOR ALBDAC
c#include "bmgrdbuf.h"
C   RADCOM NEEDED FOR DIURNAL
#include "radcom.h"

C   ANTTFLX NEEDED FOR NET LW AND SW FLUX ARRAYS (CO2FRC EXPERIMENT)
#include "anttflx.h"
C   ACO2FRC NEEDED FOR CO2FRC LOGICAL FLAG
#include "aco2frc.h"

C   SPCOMP NEEDED FOR SOLH, QRAD
#include "spcomp.h"
#include "solcom.h"
      complex qrad(JSQ,JS)
      complex solh(JSQ,JS)
C
#include "h2ofor.h"
C
      IF (DIURNAL .AND.
     *   (KOUNT.EQ.0 .OR. MOD((KOUNT-NANKNT-KOUNTR),NPREC).EQ.0)) THEN
         DO 30 IFIELD = 1,MAXCLD
            IF ((MASKAC3(IFIELD).NE.0).AND.(MASKAC3(IFIELD).NE.3))THEN
        
CJRF  Put CNVCLD into 17 temporarily, so do not treat specially
C              IF (IFIELD.NE.17.AND.IFIELD.NE.22.AND.IFIELD.NE.23) THEN
               IF (IFIELD.NE.22.AND.IFIELD.NE.23) THEN
               DO 10 I=1,nlon
                  DO 10 J=1,nlat
                  DGCFLD(I,J,IFIELD) = 0.0
10             CONTINUE
               ELSE IF(IFIELD.EQ.22.OR.IFIELD.EQ.23)THEN
               DO 15 I=1,nlon
                  DO 15 J=1,nlat
                  DGCFLD(I,J,IFIELD) = 0
15             CONTINUE
               ENDIF
            END IF
30       CONTINUE
         DO 31 IFIELD = 1,MAXVAP
            IF ((MASKAC5(IFIELD).NE.0).AND.(MASKAC5(IFIELD).NE.3))THEN
               DO 11 I=1,nlon
                  DO 11 J=1,nlat
                  H2OFLD(I,J,IFIELD) = 0.0
11             CONTINUE
             ENDIF
31       CONTINUE
C
C ...ZERO THE NET LW AND SW FLUX ARRAYS FOR CO2FRC
C
cimb LW AND SW FLUX arrays are not used
c         DO 32 I=1,nlon
c         DO 32 J=1,nlat
c         DO 32 K=1,JS+1
c                 CLDLW1(I,J,K) = 0.0
c                 CLDSW1(I,J,K) = 0.0
c                 CLRLW1(I,J,K) = 0.0
c                 CLRSW1(I,J,K) = 0.0
C
c                 CLDLW2(I,J,K) = 0.0
c                 CLDSW2(I,J,K) = 0.0
c                 CLRLW2(I,J,K) = 0.0
c                 CLRSW2(I,J,K) = 0.0
c 32      CONTINUE
C
crzc         DO 40 I=1,nlon
crzc            ALBDAC(I)=0.0
crzc40       CONTINUE
      ENDIF
CJRF  Put CNVCLD into 17 temporarily, so do not treat specially
CC Following mods have been removed from CONINZ and put in here
C      IF(KOUNT.EQ.0 .OR. MOD(KOUNT-NANKNT-1,NPREC).EQ.0) THEN
C         DO 50 I=1,nlon
C         DO 50 J=1,nlat
CC           Reset CLD COUNTER field
C	    DGCFLD(I,J,17) = 0.0
C 50      CONTINUE
C      ENDIF
C
C
C     Code from INRADG
C     only zero SOLH QRAD  every IDUMPT steps
C     so as to allow a daily average of these
C
      if ( modeltype .ne. 'laps' ) then
      if (KOUNT.EQ.0.OR.MOD(KOUNT-NANKNT-1,IDUMPT).EQ.0)THEN
      DO 35 IH=1,JS
      DO 35 IL=1,JSQ
         SOLH(IL,IH) = (0.0,0.0)
         QRAD(IL,IH) = (0.0,0.0)
   35 CONTINUE
      ENDIF
      endif
C
      RETURN
      END
