       SUBROUTINE AMIP1INT(IUSST,MTH,MYR,MTHN,MYRN,YRMEAN,
     *               WGTP,WGTN,WGTI,
     *                IXO,IYO,ANTICE,
     *              SST,SEAICE,SSTY,
     *             NLATS,NLONGS)
C
c       read in AMIP I SST data (as massaged by BMRC
C
      PARAMETER(AMISS=1.0E36)
      PARAMETER (SWICE=-1.95)
C
        DIMENSION SST(IXO,IYO),SEAICE(IXO,IYO)
        DIMENSION SSTY(IXO)
C
        LOGICAL YRMEAN
C
      IF(.NOT.YRMEAN) THEN
C
C          Variable - year by year data
C     CALCULATE STARTING RECORD OF CORREECT MONTH & YEAR
         IF(MTH.EQ.12.AND.MTHN.EQ.1)THEN
	    MYRN = MYR+1
         ELSE IF(MTH.EQ.1.AND.MTHN.EQ.12) THEN
	    MYRN = MYR-1
   	 IF(MYRN.LT.1979)THEN
   	    MYRN=1979
   	    MTHN=1
c          use dec 1979 rather than dec 1978 (which is not available)
               mthn=12
         ENDIF
         ELSE
	    MYRN = MYR
         ENDIF
C
         WRITE (6,*) 'MNTHN * MYRN ',MTHN,MYRN
      	 IST = (NLATS+1)*(MTHN-1) + (NLATS+1)*12*(MYRN-1979) + 1
C
	ELSE
C
C        Fixed Year (Mean) AMIP data
        WRITE (6,*) 'MTHN ',MTHN
	IST = NLATS*(MTHN-1)
	ENDIF
C
      	DO 56 J=1,NLATS
       	   READ(IUSST,REC=IST+J)(SSTY(I),I=1,NLONGS)
c
 9885 FORMAT(1x,10F8.3)
           IF(J.GT.NLATS/2)THEN
              THICK=2.0
           ELSE
              THICK=ANTICE
           ENDIF
      	DO 55 I=1,NLONGS
c
        IF ( SST(I,NLATS-J+1).LE.SWICE .AND. SSTY(I).LE.SWICE ) THEN
C          sea ice for both months
           continue
        ELSE IF ( SST(I,NLATS-J+1).GT.SWICE  .AND.
     &          SSTY(I).LE.SWICE	) THEN
c           no sea ice for old but is sea ice for new
           SEAICE(I,nlats-j+1)=(1.0-WGTI)*THICK
        ELSE IF ( SST(I,NLATS-J+1).LE.SWICE  .AND.
     &          SSTY(I).GT.SWICE	) THEN
c          sea ice for old mth - but not new
c           ice thickness ramps down 
           SEAICE(i,nlats-j+1)=WGTI*SEAICE(i,nlats-j+1)
       	ELSE
C          no sea ice
           SEAICE(i,nlats-j+1)=AMISS
           SST(I,NLATS-J+1) = WGTP*SST(I,NLATS-J+1) + WGTN*SSTY(I)
       	ENDIF
   55 	CONTINUE
   56 	CONTINUE
C
C
C     CONVERT SST TO DEGREES KELVIN
      DO  J=1,NLATS
      DO  I=1,NLONGS
      SST(I,J)=273.16+SST(I,J)
      END DO
      END DO
C
        RETURN
        END
