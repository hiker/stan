C*DECK ASV_DV
C @(#) $Source$
C @(#) $Name$ $Revision: 28 $ $Date: 2003-07-25 16:16:19 +1000 (Fri, 25 Jul 2003) $
      SUBROUTINE ASV_DV (POLSTH, POLNTH, RMAX, WTHGAU, NDVOL,
     @             DVLTS, DVLTN, DVLNW, DVLNE, IS, IN, IW, IE)
C
C     Determine which analysis subvolumes should be processed when
C        each data volume is in core
C
       Use MOD_PHYSPARM, only : DTR

#include "agpmetrx.h"
#include "mvparm.h"
#include "mvavol.h"
#include "mvgausll.h"
#include "mvvols.h"
#include "mvzones.h"
#include "prjpar.h"
#include "multsi.h"
C
C Input Parameters :
C     POLSTH     : If zero, the southern hemisphere is one data volume
C                  If negative, the southern hemisphere not analyzed
C                  If positive, the area poleward of POLSTH is 1 volume
C     POLNTH     : If zero, the northern hemisphere is one data volume
C                  If negative, the northern hemisphere not analyzed
C                  If positive, the area poleward of POLNTH is 1 volume
C     RMAX       : Maximum radius for data selection
C     WTHGAU     : Gap between neighbouring longitudes
C     NDVOL      : Number of data volumes
C     DVLTS      : Southern boundary for each data volume
C     DVLTN      : Northern boundary for each data volume
C     DVLNW      : Western boundary for each data volume
C     DVLNE      : Eastern boundary for each data volume
C   IS,IN,IW,IE  : Boundaries of analysis volumes
C        (Indices of Gaussian lats and longitudes)
C
      REAL      POLSTH, POLNTH, RMAX, WTHGAU
      INTEGER   NDVOL
      REAL      DVLTS(MDVOL), DVLTN(MDVOL), DVLNW(MDVOL), DVLNE(MDVOL)
      INTEGER   IS(MASV), IN(MASV), IW(MASV), IE(MASV)
C
C Local variables :
C     KPDV       : ??
C     DWTHIN     : ??
C
      INTEGER   KPDV(MASV)
C      REAL      DWTHIN(MASV), CWTHIN(MASV)
C
C     For each analysis subvolume, determine if it lies wholly within
C        the latitude-longitude bounds of a data volume
C         and if so how far...
C
C     LOOP over analysis subvolumes...

      DO KA=1,KAVOL
        KPDV(KA)=-9999
C        DWTHIN(KA)=-9999.
        DMAX=0.0
        ASLT=GAUSLT(IS(KA))
        ANLT=GAUSLT(IN(KA))
C
        If ( .NOT. LIMAR ) Then
C          Check whether analysis subvolume within polar cap data volume...
           AVLT=0.5*(ASLT+ANLT)
           IF ( (AVLT-RMAX) .GT. POLSTH ) THEN
             DMAX=9999.
C             CWTHIN(KA)=9999.
C             DWTHIN(KA)=9999.
             KPDV(KA)=1
           ELSE IF ( (AVLT+RMAX) .LT. (-POLNTH) ) THEN
             DMAX=9999.
C             CWTHIN(KA)=9999.
C             DWTHIN(KA)=9999.
             KPDV(KA)=MDVOL
           ENDIF
        ENDIF

        AWLN=(IW(KA)-1)*WTHGAU + SLON
        AELN=(IE(KA)-1)*WTHGAU + SLON
        WG=(IE(KA)-IW(KA))*WTHGAU
        IF (WG .LT. 0.0) WG=WG+360.
        AVLTA=ABS(0.5*(ASLT+ANLT)) * DTR
C
C       LOOP over data volumes...
        DO KD=1,NDVOL
          WD=DVLNE(KD)-DVLNW(KD)
          IF (WD .LT. 0.0) WD=WD+360.
          IF ( ASLT.LT.DVLTS(KD) .AND. ANLT.GT.DVLTN(KD) )THEN
            IF ( CWDISP(DVLNW(KD),AWLN).LT.(WD-WG) .OR.
     @           DVLNW(KD).EQ.0.0 .AND. DVLNE(KD).EQ.360. ) THEN
C
C           Analysis subvolume is completely within data volume...
              DISTN=ABS(ANLT-DVLTN(KD))
              DISTS=ABS(ASLT-DVLTS(KD))
              DISTMN=AMIN1(DISTN,DISTS)
              DISNSC=DISTMN+0.5*ABS(ASLT-ANLT)
              IF ( DVLNW(KD).NE.0.0 .OR. DVLNE(KD).NE.360.0 ) THEN
C
C             For sector data volume, compute distance
C                 inside e-w boundaries...
                DISTW=ABS(AWLN-DVLNW(KD))
                IF (DISTW .GT. 180.0) DISTW=360.-DISTW
                DISTW=DISTW*COS(AVLTA)
                DISTE=ABS(AELN-DVLNE(KD))
                IF (DISTE .GT. 180.0) DISTE=360.-DISTE
                DISTE=DISTE*COS(AVLTA)
C                DISWEC=AMIN1(DISTE,DISTW)+0.5*WG*COS(AVLTA)
                DISTMN=AMIN1(DISTMN,DISTE,DISTW)
              ENDIF
C
C             Determine whether the distance DISTMN inside the
C               data volume boundary is the greatest so far...
              IF (DISTMN .GT. DMAX) THEN
                DMAX=DISTMN
                KPDV(KA)=KD
C                DWTHIN(KA)=DMAX
C               Calculate corresponding distance of analysis
C                 subvolume centre from edge of data volume...
C                CWTHIN(KA)=AMIN1(DISNSC,DISWEC)
              ENDIF
            ENDIF
          ENDIF
C
C       END LOOP over data volumes...(KD = 1,NDVOL)
C
        END DO
C
C     END LOOP over analysis subvolumes...(KA = 1,KAVOL)
C
      END DO
C
C
C     For each data volume, determine the number of analysis subvolumes
C      belonging to it, and their indices...
C
C
      DO KD=1,NDVOL
        KNT=0
C       PRINT *,' KD= ',KD,DVLTS(KD),DVLTN(KD),DVLNW(KD),DVLNE(KD)
        DO KA = 1, MASVDV
          IANVOL(KA,KD) = -1
        END DO
        DO KA=1,KAVOL
          IF (KPDV(KA) .EQ. KD) THEN
            KNT=KNT+1
            IF (KNT .GT. MASVDV) THEN
              PRINT *,' MASVDV TOO SMALL'
              call abstop
            ENDIF
            IANVOL(KNT,KD)=KA
            DO 100 L=1,NBOX(NZON,KA)
              DO N=1,NBOXD(KD)
                IF (IBOXD(N,KD) .EQ. IBOX(KA,NZON,L)) GO TO 100
              END DO
              PRINT *,' DATA FOR 10X10 BOX NUMBER ',IBOX(KA,NZON,L),
     @           ' NOT AVAILABLE FOR ANALYSIS OF SUBVOLUME ',KA,
     @           ' USING DATA VOLUME ',KD
  100       CONTINUE
          ENDIF
        END DO
        KANVOL(KD)=KNT
        PRINT 6000,KNT,KD
 6000   FORMAT(//,' THE FOLLOWING',I4,' ANALYSIS SUBVOLUMES WILL BE',
     @       ' PROCESSED WHEN DATA FOR DATA VOLUME',I3,' ARE IN CORE')
C       PRINT *,' KD,KANVOL ',KD,KNT
        PRINT *,' SUBVOLUMES ',(IANVOL(I,KD),I=1,KNT)
      END DO
C
      RETURN
      END

C      CHARACTER(LEN=*) FUNCTION ASV_DV_RCS_ID()
C
C      ASV_DV_RCS_ID = 
C     > '$Id: asv_dv.F 28 2003-07-25 06:16:19Z joh $' 
C
C      Return 
C      End 
