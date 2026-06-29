# Mock Grading Questions Report

## Summary

| Metric | Value |
|---|---:|
| Total questions | 10 |
| Success rate | 100.00% |
| Top-1 retrieval accuracy | 100.00% |
| Required answer rate | 100.00% |

## Results

| Question | Expected doc | Actual doc | Required answer | Forbidden terms | Success |
|---|---|---|---:|---:|---:|
| gq_d10_01 | policy_refund_v4 | policy_refund_v4 | yes | no | yes |
| gq_d10_02 | policy_refund_v4 | policy_refund_v4 | yes | no | yes |
| gq_d10_03 | policy_refund_v4 | policy_refund_v4 | yes | no | yes |
| gq_d10_04 | sla_p1_2026 | sla_p1_2026 | yes | no | yes |
| gq_d10_05 | sla_p1_2026 | sla_p1_2026 | yes | no | yes |
| gq_d10_06 | sla_p1_2026 | sla_p1_2026 | yes | no | yes |
| gq_d10_07 | it_helpdesk_faq | it_helpdesk_faq | yes | no | yes |
| gq_d10_08 | it_helpdesk_faq | it_helpdesk_faq | yes | no | yes |
| gq_d10_09 | hr_leave_policy | hr_leave_policy | yes | no | yes |
| gq_d10_10 | access_control_sop | access_control_sop | yes | no | yes |

## Answers
### gq_d10_01
**Question:** Theo chính sách hoàn tiền hiện hành, khách hàng có tối đa bao nhiêu ngày làm việc để gửi yêu cầu hoàn tiền sau khi đơn được xác nhận?
**Answer:** Chính sách hoàn tiền hiện hành cho phép khách hàng gửi yêu cầu hoàn tiền tối đa 7 ngày làm việc sau khi đơn được xác nhận. (Nguồn: policy_refund_v4)

### gq_d10_02
**Question:** Đâu là loại sản phẩm bị loại khỏi điều kiện hoàn tiền?
**Answer:** Các sản phẩm bị loại khỏi điều kiện hoàn tiền gồm hàng kỹ thuật số, license key và subscription. (Nguồn: policy_refund_v4)

### gq_d10_03
**Question:** Finance Team xử lý yêu cầu hoàn tiền trong bao lâu?
**Answer:** Finance Team xử lý yêu cầu hoàn tiền trong 3-5 ngày làm việc sau khi hồ sơ hợp lệ. (Nguồn: policy_refund_v4)

### gq_d10_04
**Question:** SLA phản hồi ban đầu cho ticket P1 là bao lâu?
**Answer:** Ticket P1 có SLA phản hồi ban đầu là 15 phút. (Nguồn: sla_p1_2026)

### gq_d10_05
**Question:** SLA resolution cho ticket P1 là bao nhiêu giờ?
**Answer:** SLA resolution cho ticket P1 là 4 giờ. (Nguồn: sla_p1_2026)

### gq_d10_06
**Question:** Nếu không có phản hồi với ticket P1 sau bao lâu thì hệ thống auto escalate?
**Answer:** Nếu không có phản hồi với ticket P1 sau 10 phút thì hệ thống auto escalate cho on-call manager. (Nguồn: sla_p1_2026)

### gq_d10_07
**Question:** Tài khoản bị khóa sau bao nhiêu lần đăng nhập sai liên tiếp?
**Answer:** Tài khoản bị khóa sau 5 lần đăng nhập sai liên tiếp. (Nguồn: it_helpdesk_faq)

### gq_d10_08
**Question:** VPN cho phép kết nối tối đa bao nhiêu thiết bị cùng lúc?
**Answer:** VPN cho phép kết nối tối đa 2 thiết bị cùng lúc cho mỗi nhân viên. (Nguồn: it_helpdesk_faq)

### gq_d10_09
**Question:** Nhân viên dưới 3 năm kinh nghiệm được bao nhiêu ngày phép năm theo chính sách HR 2026?
**Answer:** Theo chính sách HR 2026, nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm. (Nguồn: hr_leave_policy)

### gq_d10_10
**Question:** Level 4 Admin Access yêu cầu phê duyệt bởi ai?
**Answer:** Level 4 Admin Access yêu cầu phê duyệt bởi IT Manager và CISO trước khi cấp quyền. (Nguồn: access_control_sop)

