function [jrt, jst]=jacprojRTS(j, i, rt, xyz, r0, a)
% symbolic projection function Jacobian
% code automatically generated with maple

  qr0=r0(j*4+1:(j+1)*4);

  t1 = (rt(1) ^ 2);
  t2 = (rt(2) ^ 2);
  t3 = (rt(3) ^ 2);
  t5 = sqrt((1 - t1 - t2 - t3));
  t6 = 0.1e1 / t5;
  t7 = t6 * qr0(2);
  t9 = -t7 * rt(1) + qr0(1);
  t11 = t6 * qr0(3);
  t13 = -t11 * rt(1) - qr0(4);
  t15 = t6 * qr0(4);
  t17 = -t15 * rt(1) + qr0(3);
  t19 = -t9 * xyz(1) - t13 * xyz(2) - t17 * xyz(3);
  t24 = -t5 * qr0(2) - qr0(1) * rt(1) - rt(2) * qr0(4) + rt(3) * qr0(3);
  t31 = t5 * qr0(3) + qr0(1) * rt(2) + rt(3) * qr0(2) - rt(1) * qr0(4);
  t37 = t5 * qr0(4) + qr0(1) * rt(3) + rt(1) * qr0(3) - rt(2) * qr0(2);
  t39 = t24 * xyz(1) - t31 * xyz(2) - t37 * xyz(3);
  t41 = t6 * qr0(1);
  t43 = -t41 * rt(1) - qr0(2);
  t48 = t5 * qr0(1) - rt(1) * qr0(2) - rt(2) * qr0(3) - rt(3) * qr0(4);
  t52 = t48 * xyz(1) + t31 * xyz(3) - t37 * xyz(2);
  t57 = t43 * xyz(1) + t13 * xyz(3) - t17 * xyz(2);
  t62 = t43 * xyz(2) + t17 * xyz(1) - t9 * xyz(3);
  t67 = t48 * xyz(2) + t37 * xyz(1) + t24 * xyz(3);
  t72 = t43 * xyz(3) + t9 * xyz(2) - t13 * xyz(1);
  t77 = t48 * xyz(3) - t24 * xyz(2) - t31 * xyz(1);
  t89 = -t19 * t31 - t39 * t13 + t43 * t67 + t48 * t62 + t72 * t24 - t77 * t9 + t57 * t37 + t52 * t17;
  t99 = -t19 * t37 - t39 * t17 + t43 * t77 + t48 * t72 - t57 * t31 - t52 * t13 - t62 * t24 + t67 * t9;
  t106 = -t39 * t37 + t48 * t77 - t52 * t31 - t67 * t24 + rt(6);
  t107 = 0.1e1 / t106;
  t119 = -t39 * t31 + t48 * t67 + t77 * t24 + t52 * t37 + rt(5);
  t123 = t106 ^ 2;
  t124 = 0.1e1 / t123;
  t125 = (a(1) * (t39 * t24 + t48 * t52 - t67 * t37 + t77 * t31 + rt(4)) + a(2) * t119 + a(3) * t106) * t124;
  t129 = -t7 * rt(2) + qr0(4);
  t132 = -t11 * rt(2) + qr0(1);
  t135 = -t15 * rt(2) - qr0(2);
  t137 = -t129 * xyz(1) - t132 * xyz(2) - t135 * xyz(3);
  t141 = -t41 * rt(2) - qr0(3);
  t146 = t141 * xyz(1) + t132 * xyz(3) - t135 * xyz(2);
  t151 = t141 * xyz(2) + t135 * xyz(1) - t129 * xyz(3);
  t157 = t141 * xyz(3) + t129 * xyz(2) - t132 * xyz(1);
  t170 = -t137 * t31 - t39 * t132 + t141 * t67 + t48 * t151 + t157 * t24 - t77 * t129 + t146 * t37 + t52 * t135;
  t180 = -t137 * t37 - t39 * t135 + t141 * t77 + t48 * t157 - t146 * t31 - t52 * t132 - t151 * t24 + t67 * t129;
  t187 = -t7 * rt(3) - qr0(3);
  t190 = -t11 * rt(3) + qr0(2);
  t193 = -t15 * rt(3) + qr0(1);
  t195 = -t187 * xyz(1) - t190 * xyz(2) - t193 * xyz(3);
  t199 = -t41 * rt(3) - qr0(4);
  t204 = t199 * xyz(1) + t190 * xyz(3) - t193 * xyz(2);
  t209 = t199 * xyz(2) + t193 * xyz(1) - t187 * xyz(3);
  t215 = t199 * xyz(3) + t187 * xyz(2) - t190 * xyz(1);
  t228 = -t195 * t31 - t39 * t190 + t199 * t67 + t48 * t209 + t215 * t24 - t77 * t187 + t204 * t37 + t52 * t193;
  t238 = -t195 * t37 - t39 * t193 + t199 * t77 + t48 * t215 - t204 * t31 - t52 * t190 - t209 * t24 + t67 * t187;
  t255 = (a(4) * t119 + a(5) * t106) * t124;
  jrt(1) = (a(1) * (t19 * t24 - t39 * t9 + t43 * t52 + t48 * t57 - t62 * t37 - t67 * t17 + t72 * t31 + t77 * t13) + a(2) * t89 + a(3) * t99) * t107 - t125 * t99;
  jrt(2) = (a(1) * (t137 * t24 - t39 * t129 + t141 * t52 + t48 * t146 - t151 * t37 - t67 * t135 + t157 * t31 + t77 * t132) + a(2) * t170 + a(3) * t180) * t107 - t125 * t180;
  jrt(3) = (a(1) * (t195 * t24 - t39 * t187 + t199 * t52 + t48 * t204 - t209 * t37 - t67 * t193 + t215 * t31 + t77 * t190) + a(2) * t228 + a(3) * t238) * t107 - t125 * t238;
  jrt(4) = a(1) * t107;
  jrt(5) = a(2) * t107;
  jrt(6) = a(3) * t107 - t125;
  jrt(7) = (a(4) * t89 + a(5) * t99) * t107 - t255 * t99;
  jrt(8) = (a(4) * t170 + a(5) * t180) * t107 - t255 * t180;
  jrt(9) = (a(4) * t228 + a(5) * t238) * t107 - t255 * t238;
  jrt(10) = 0.0e0;
  jrt(11) = a(4) * t107;
  jrt(12) = a(5) * t107 - t255;

  t1 = (rt(1) ^ 2);
  t2 = (rt(2) ^ 2);
  t3 = (rt(3) ^ 2);
  t5 = sqrt((1 - t1 - t2 - t3));
  t10 = -t5 * qr0(2) - qr0(1) * rt(1) - rt(2) * qr0(4) + rt(3) * qr0(3);
  t11 = t10 ^ 2;
  t16 = t5 * qr0(1) - rt(1) * qr0(2) - rt(2) * qr0(3) - rt(3) * qr0(4);
  t17 = t16 ^ 2;
  t22 = t5 * qr0(4) + qr0(1) * rt(3) + rt(1) * qr0(3) - rt(2) * qr0(2);
  t28 = -t5 * qr0(3) - qr0(1) * rt(2) - rt(3) * qr0(2) + rt(1) * qr0(4);
  t29 = t28 ^ 2;
  t32 = t10 * t28;
  t35 = -t16 * t22;
  t36 = 0.2e1 * t32 + t16 * t22 - t35;
  t38 = -t10 * t22;
  t39 = t16 * t28;
  t42 = t38 + 0.2e1 * t39 - t10 * t22;
  t48 = t10 * xyz(1) + t28 * xyz(2) - t22 * xyz(3);
  t53 = t16 * xyz(3) - t10 * xyz(2) + t28 * xyz(1);
  t58 = t16 * xyz(1) - t28 * xyz(3) - t22 * xyz(2);
  t63 = t16 * xyz(2) + t22 * xyz(1) + t10 * xyz(3);
  t65 = -t48 * t22 + t16 * t53 + t58 * t28 - t63 * t10 + rt(6);
  t66 = 0.1e1 / t65;
  t78 = t48 * t28 + t16 * t63 + t53 * t10 + t58 * t22 + rt(5);
  t82 = t65 ^ 2;
  t83 = 0.1e1 / t82;
  t84 = (a(1) * (t48 * t10 + t16 * t58 - t63 * t22 - t53 * t28 + rt(4)) + a(2) * t78 + a(3) * t65) * t83;
  t92 = t22 ^ 2;
  t93 = t29 + t17 - t10 ^ 2 - t92;
  t95 = -t28 * t22;
  t98 = t16 * t10;
  t99 = 0.2e1 * t95 - t16 * t10 - t98;
  t111 = t95 + 0.2e1 * t98 - t28 * t22;
  t114 = t92 + t17 - t28 ^ 2 - t11;
  t127 = (a(4) * t78 + a(5) * t65) * t83;
  jst(1) = (a(1) * (t11 + t17 - t22 ^ 2 - t29) + a(2) * t36 + a(3) * t42) * t66 - t84 * t42;
  jst(2) = (a(1) * (t32 + 0.2e1 * t35 + t10 * t28) + a(2) * t93 + a(3) * t99) * t66 - t84 * t99;
  jst(3) = (a(1) * (0.2e1 * t38 - t16 * t28 - t39) + a(2) * t111 + a(3) * t114) * t66 - t84 * t114;
  jst(4) = (a(4) * t36 + a(5) * t42) * t66 - t127 * t42;
  jst(5) = (a(4) * t93 + a(5) * t99) * t66 - t127 * t99;
  jst(6) = (a(4) * t111 + a(5) * t114) * t66 - t127 * t114;
