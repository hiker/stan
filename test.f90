subroutine test_prog()
  integer :: a, b, c, d
  a = b + c/(d+e)**fx
  do k = 0, nlayers
    exner = exner_in_wth(map_wth(1) + k)
    sigma = (exner/exner0)**(1.0_r_def/kappa)
    theta_eq = tidally_locked_earth_equilibrium_theta(exner, lon, lat)
    dtheta(map_wth(1) + k) = -held_suarez_newton_frequency(sigma, lat) * (theta(map_wth(1) + k) - theta_eq) * dt
  end do
  theta_eq = max(T_MIN/exner, (T_SURF - DT_EQ_POLE*sin(lat)*sin(lat) - STATIC_STABILITY*log(exner)*cos(lat)*cos(lat)/kappa))
        j_xi = matmul(jac(:,:,qp1,qp2),xi_at_quad)/dj(qp1,qp2)
        j_u  = matmul(jac(:,:,qp1,qp2),u_at_quad)/dj(qp1,qp2)
        vorticity = cross_product(j_xi, j_u)
     if ( d > 0.0_r_tran ) then
        x1 = (-b+sqrt(d))/(2.0_r_tran*a + EPS_R_TRAN)
        x2 = (-b-sqrt(d))/(2.0_r_tran*a + EPS_R_TRAN)
        v1 = a0(i) + a1(i)*x1 + a2(i)*(x1**2) + a3(i)*(x1**3)
        v2 = a0(i) + a1(i)*x2 + a2(i)*(x2**2) + a3(i)*(x2**3)
     end if
  xn1 = xn1/sqrt(xn1(1)**2 + xn1(2)**2 + xn1(3)**2)
  fn = (xx(1)**px)*(xx(2)**py)
end subroutine test_prog
