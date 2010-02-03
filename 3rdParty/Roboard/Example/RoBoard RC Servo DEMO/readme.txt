This is a large demo program, called RoBoRC (RoBoard RC servo DEMO), for RoBoIO's RCservo lib.
Its source code can be found in the RoBoIO source release.

This program can capture positions of (ex. KONDO, HiTEC) servo motors,
and then replay the servo positions afterward.
You can also write scripts to make your (KONDO, HiTEC) robots play rich moves.

Video for some examples of using RoBoRC can be seen on Youtube:

    http://www.youtube.com/watch?v=FT3sfjKDhv4
    http://www.youtube.com/watch?v=eE7dPp1iyMQ


For a brief help, run RoBoRC.exe without argument.


------------------------------------------------------------
guide for running the RoBoRC.exe on DMP X-Linux R5.5/R5.6:

1. in X-Linux, type:
       rw
   for remounting the file system to allow read/write

2. copy "vt100" to "/usr/share/terminfo/v/" (mkdir it, if it doesn't exist) at X-Linux

3. type:
       export TERM=vt100

4. copy and then run ./RoBoRC.exe in X-Linux to see some brief usage examples.
